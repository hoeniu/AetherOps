from agno.agent import Agent
from kbx.common.utils import doc_element_to_markdown
from kbx.common.prompt import get_category_prompts
from typing import Iterator, List, Dict
from kbx.common.types import DocData
from textwrap import dedent
import os
import time
import json
from typing import List, Dict, Any
import yaml

from kbx.common.utils import doc_data_to_markdown
from kbx.parser.parser_factory import SmartParser
from kbx.common.types import DocFileType, KBXError
from kbx.common.constants import DEFAULT_USER_ID
from kbx.kbx import KBX
from kbx.knowledge_base.types import (
    KBCreationConfig,
    SplitterConfig,
    QueryConfig,
    VectorKeywordIndexConfig,
    QueryResults,
    Chunk
)
from kbx.common.utils import generate_new_id
from kbx.rerank.types import RerankConfig
from kbx.parser.types import DocParseConfig
from kbx.agent.types import AgentConfig
from kbx.common.logging import logger

from kbx.splitter.splitter_factory import get_splitter
from kbx.splitter.types import SplitterConfig


class BaseProcessor:
    """基础文档处理器

    提供文档处理的基础功能，包括：
    1. 知识库的创建和管理
    2. 大模型的调用
    3. 文档格式转换
    4. 性能监控
    """

    def __init__(self,
                 kb_name: str = "标书知识库",
                 kb_description: str = "这是一个运维知识库，doc 格式",
                 llm_model: str = 'volcengine-deepseek-v3'):
        """初始化基础文档处理器

        Args:
            kb_name: 知识库名称
            kb_description: 知识库描述
        """
        self._kb_name = kb_name
        self._kb_description = kb_description
        self._kb = None
        self.kbx_yaml_file = None
        self.ai_models_yaml_file = None
        # self.root_dir = os.path.join(os.path.dirname(
        #     os.path.abspath(__file__)), '../..')
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self._kbx_setup()
        self._client_config, self._client = KBX.get_ai_model_config_and_client(
            llm_model)

        # 按模型max_context_len来设置chunk_size
        # MIN_CHUNK_SIZE = 1024 * 4
        # MAX_CHUNK_SIZE = 1024 * 10  # 设置太大会找不到内容
        # self.chunk_size = max(
        #     min(self._client_config.max_context_len - 1024 * 8, MAX_CHUNK_SIZE), MIN_CHUNK_SIZE)
        self.chunk_size = 1024
        from kbx.common.token_counter.token_counter_factory import get_token_counter
        from kbx.common.types import TokenCounterConfig
        self.token_counter = get_token_counter(TokenCounterConfig(counter="estimated"))

        # 设置环境变量和目录
        self._setup_directories()

    def _setup_directories(self):
        """设置必要的目录路径"""
        self.tender_data_dir = os.environ.get('TENDER_DATA_DIR', os.path.join(
            self.root_dir, './data/upload_files'))  # 上传的标书文件目录，默认将此目录存放的文件插入知识库
        self.md_data_dir = os.environ.get('MD_DATA_DIR', os.path.join(
            self.root_dir, './data/markdown'))  # 转换后的markdown文件目录
        self.output_dir = os.environ.get('OUTPUT_DIR', os.path.join(
            self.root_dir, './data/extracted_results'))  # 提取结果目录
        self.extra_doc_elements_dir = os.environ.get('EXTRA_DOC_ELEMENTS_DIR', os.path.join(
            self.root_dir, './data/extra_doc_elements'))  # 额外文档元素目录

        # 确保目录存在
        for directory in [self.tender_data_dir, self.md_data_dir, self.output_dir, self.extra_doc_elements_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def _kbx_setup(self):
        """初始化KBX配置"""

        # 设置默认配置文件路径
        if not self.kbx_yaml_file:
            self.kbx_yaml_file = os.path.join(
                self.root_dir, './config/kbx_settings.yaml')
        if not self.ai_models_yaml_file:
            self.ai_models_yaml_file = os.path.join(
                self.root_dir, './config/ai_models.yaml')

        # 初始化KBX
        if self.kbx_yaml_file:
            KBX.init(config=self.kbx_yaml_file)
        if self.ai_models_yaml_file:
            KBX.register_ai_models_from_conf(
                model_configs=self.ai_models_yaml_file, overwrite=True)

    def create_knowledge_base(self,
                              config_file_path: str = 'config/create_vector_kb.yaml',
                              doc_path: str = None,
                              chunk_size: int = None
                              ) -> None:
        """创建知识库

        Args:
            config_file_path: 配置文件路径
            doc_path: 文档路径
            chunk_size: 文档分块大小，默认为None
        """
        kb_start_time = time.time()

        # 首先创建一个使用默认值的KBCreationConfig对象
        kb_config = KBCreationConfig()

        if config_file_path.endswith('.yaml') or config_file_path.endswith('.yml'):
            # Read and parse YAML config file
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
        elif config_file_path.endswith('.json'):
            # Read and parse JSON config file
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
        else:
            raise ValueError(
                f"Invalid config file \"{config_file_path}\". Please provide a YAML or JSON file.")

        # 使用model_validate方法更新配置，只更新config_dict中存在的字段
        if config_dict:
            kb_config = kb_config.model_validate(
                {**kb_config.model_dump(), **config_dict})
        # 设置chunk_size
        if chunk_size is not None:
            kb_config.vector_keyword_config.splitter_config.chunk_size = chunk_size
        else:
            kb_config.vector_keyword_config.splitter_config.chunk_size = self.chunk_size

        print(f'创建知识库时chunk_size: {kb_config.vector_keyword_config.splitter_config.chunk_size}')
        # 如果知识库已存在，先删除
        if self._kb:
            return
        try:
            previous_kb = KBX.get_existed_kb(
                kb_name=kb_config.name, user_id=DEFAULT_USER_ID)
            previous_kb.remove_kb()
        except RuntimeError:
            pass

        # 创建新知识库
        self._kb = KBX.create_new_kb(kb_config, user_id=DEFAULT_USER_ID)
        logger.info(f'Created new kb {kb_config.name} (id={self._kb.kb_id})')

        # 插入文档
        if not os.path.isfile(doc_path):
            raise ValueError(f"doc_path must be a file path, not a directory: {doc_path}")
        all_files = [doc_path]
        results = self._kb.insert_docs(file_list=all_files)
        if any([doc_info.err_info.code != KBXError.Code.SUCCESS for doc_info in results]):
            raise RuntimeError(
                f"Failed to insert docs to knowledge base:\n{results}")

        kb_time = time.time() - kb_start_time
        logger.info(f"Knowledge base creation took {kb_time:.2f} seconds")

    def parse_and_split(self, docx_path: str, chunk_size: int = None):
        """解析和分割文档"""
        doc_parse_config = DocParseConfig()
        parser = SmartParser(doc_parse_config)
        
        doc_id = generate_new_id()
        docdata = parser.parse(file_path=docx_path, doc_id=doc_id)
        
        splitter = get_splitter(
            SplitterConfig(name="NaiveTextSplitter",
                           chunk_size=chunk_size,
                           overlap_size=0))
        chunks = splitter.split(docdata)
        return docdata, chunks

    def convert_docx_to_markdown(self, docx_path: str, prepend_file_name: bool = False) -> str:
        """将docx文件转换为markdown格式

        Args:
            docx_path: docx文件路径
            prepend_file_name: 是否在markdown内容前添加文件名
        Returns:
            str: markdown格式的文本内容
        """
        docx_start_time = time.time()

        # kb_config = KBCreationConfig()
        # _kb = KBX.create_new_kb(kb_config, user_id=DEFAULT_USER_ID)
        # all_files = [os.path.join(docx_path, file) for file in os.listdir(docx_path)]
        # results = _kb.insert_docs(file_list=all_files)

        # doc_id = os.path.basename(docx_path)
        doc_id = generate_new_id()
        # extra_doc_elements_path = os.path.join(self.extra_doc_elements_dir, doc_id)
        # os.makedirs(extra_doc_elements_path, exist_ok=True)
        doc_parse_config = DocParseConfig()
        parser = SmartParser(doc_parse_config)
        docdata = parser.parse(file_path=docx_path, doc_id=doc_id)

        # from ipdb import set_trace
        # set_trace()
        doc_content_str = doc_data_to_markdown(
            docdata, mode='original', prepend_file_name=prepend_file_name)

        docx_time = time.time() - docx_start_time
        logger.info(f"Document conversion took {docx_time:.2f} seconds")

        return doc_content_str

    def call_llm(self, system_prompt: str, user_input: str, stream: bool = False) -> str:
        """调用大模型

        Args:
            system_prompt: 系统提示词
            user_input: 用户输入

        Returns:
            str: 模型响应
        """
        llm_start_time = time.time()

        response = self._client.chat(
            self._client_config,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_input},
            ],
            stream=stream
        ).choices[0].message.content

        llm_time = time.time() - llm_start_time
        logger.info(f"LLM call took {llm_time:.2f} seconds")

        return response
    
    def test_speed_of_llm(self, system_prompt: str, text_from_chunk: str) -> Dict[str, float]:
        """测试大模型首token延迟和生成速度

        Args:
            system_prompt: 系统提示词
            text_from_chunk: 要处理的文本

        Returns:
            Dict[str, float]: 性能指标字典，包含以下指标：
                - first_token_latency: 首token延迟（毫秒）
                - generation_speed: 生成速度（tokens/s）
                - time_per_token: 每个token耗时（毫秒）
                - total_tokens: 总token数
                - chunk_tokens: chunk的token数
        """
        level2_tags = ['招标文件', '投标文件', '评标文件', '中标文件', '合同文件', '其他']
        tag_explanation = '根据文本内容，判断文本属于哪种文件类型'
        user_input = json.dumps({
            'tag_list': list(level2_tags),
            'tag_explanation': tag_explanation,
            'text': text_from_chunk,
        }, ensure_ascii=False)
        
        request_start_time = time.time()
        # response = self.call_llm(system_prompt, user_input, stream=True)
        response = self.call_llm(system_prompt, text_from_chunk, stream=True)
        
        i = 0
        total_tokens = 0
        token_timestamps = []
        first_token_received = False
        generated_text = ""
        first_token_time = None
        
        for res in response:
            content = res.choices[0].delta.content
            if content:
                num_token = self.token_counter(content)
                total_tokens += num_token
                if not first_token_received:
                    first_token_time = time.time()
                    first_token_received = True
                    
                i += 1
                token_timestamps.append(time.time())
                generated_text += content
                
        metrics = {}
        if first_token_time is not None and len(token_timestamps) > 0:
            # 首 Token 延迟（请求开始到第一个 Token）
            first_token_latency = (first_token_time - request_start_time) * 1000  # 毫秒
            # 生成阶段耗时（第一个 Token 到最后一个 Token）
            generation_time = token_timestamps[-1] - first_token_time
            
            # 生成阶段 Token 数量（排除首 Token）
            generation_token_count = len(token_timestamps) - 1
            
            # 计算生成速度
            if generation_time > 0:
                tps = generation_token_count / generation_time
                time_per_token = generation_time / generation_token_count * 1000  # 毫秒
            else:
                tps = float('inf')
                time_per_token = 0

            # 收集性能指标
            metrics = {
                'first_token_latency': first_token_latency,
                'generation_speed': tps,
                'time_per_token': time_per_token,
                'total_tokens': total_tokens,
                'chunk_tokens': self.token_counter(text_from_chunk)
            }

        return metrics

    async def call_llm_async(self, system_prompt: str, user_input: str) -> str:
        """异步调用大模型接口

        Args:
            system_prompt: 系统提示词
            user_input: 用户输入

        Returns:
            大模型的响应文本
        """
        start_time = time.time()
        try:
            response = await self._client.chat_async(
                self._client_config,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            end_time = time.time()
            logger.info(f"大模型调用耗时: {end_time - start_time:.2f}秒")
            return response
        except Exception as e:
            logger.error(f"调用大模型失败: {e}")
            raise

    def get_all_chunks(self) -> List[Chunk]:
        """获取知识库中的所有文档块

        Returns:
            List[Chunk]: 文档块列表
        """
        chunks_start_time = time.time()

        doc_ids, _ = self._kb.list_doc_ids()  # 该接口在新版KBX中，返回值变为Tuple
        logger.info(f"Found {len(doc_ids)} documents in knowledge base")

        all_chunks = []
        for doc_id in doc_ids:
            chunks, total_count = self._kb.list_chunks(doc_id, offset=0, limit=-1)
            for chunk, error in chunks:
                if error.code == KBXError.Code.SUCCESS and chunk is not None:
                    all_chunks.append(chunk)

        chunks_time = time.time() - chunks_start_time
        logger.info(
            f"Found {len(all_chunks)} chunks in {chunks_time:.2f} seconds")

        return all_chunks

    def save_json(self, data: Any, file_path: str):
        """把实例数据保存为JSON文件

        Args:
            data: 要保存的数据，可以是普通对象、Pydantic模型或者包含Pydantic模型的列表/字典
            file_path: 保存路径
        """

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 处理Pydantic模型
        def convert_pydantic_to_dict(obj):
            if hasattr(obj, 'model_dump'):  # Pydantic v2
                return obj.model_dump()
            elif hasattr(obj, 'dict'):  # Pydantic v1
                return obj.dict()
            elif isinstance(obj, list):
                return [convert_pydantic_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_pydantic_to_dict(v) for k, v in obj.items()}
            else:
                return obj

        # 转换数据
        converted_data = convert_pydantic_to_dict(data)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)

    def save_md(self, md_path: str, md_content: str):
        """保存markdown内容到文件

        Args:
            md_path: 保存路径
            md_content: markdown内容
        """
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

    def split_doc_to_batches(self, doc_data: DocData) -> Iterator[List[Dict[str, str]]]:
        """不建立知识库，将长文档分割成N个顺序的的batch doc elements，用于后续的遍历处理

        Args:
            doc_data (DocData): 需要分割的文档数据

        Returns:
            Iterator[List[Dict[str, str]]]: 返回一个包含Batch数据的迭代器，每个Batch都是一个列表，
                列表中每个元素是一个字典，字典格式为：
                {
                    "id": str,
                    "type": str,
                    "content": str
                }
        """
        # TODO：暂时使用一个简单的按顺序累积doc elements直到达到chunk size的实现，未来可以考虑进行优化

        chunk_list = []
        chunk_token_count = 0
        # NOTE: 这里需要使用深拷贝，否则外部在收到返回值后立马修改doc_data.doc_elements
        for doc_element in doc_data.doc_elements.model_copy(deep=True):
            md_text = doc_element_to_markdown(
                doc_element=doc_element, mode='original')
            doc_element_token_count = self.token_counter(md_text)

            if len(chunk_list) > 0 and chunk_token_count + doc_element_token_count > self.chunk_size:
                # 如果当前chunk_list非空，且加上当前doc_element后超过chunk_size，则yield当前chunk_list
                yield chunk_list
                chunk_list = []
                chunk_token_count = 0

            chunk_list.append(
                {
                    'id': doc_element.doc_element_id,
                    'type': doc_element.type.value,
                    'content': md_text
                }
            )
            chunk_token_count += doc_element_token_count

        if chunk_list:
            yield chunk_list
