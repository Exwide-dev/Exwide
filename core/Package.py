from typing import Dict, Any, List
import os
import sys
from core.Error import raise_err, EW_RUNTIME_ERROR
from core.Type import EW_Type

class EW_Package(EW_Type):
    """Exwide包类型"""
    
    def __init__(self, name: str, functions: Dict[str, Any]):
        self.name = name
        self.functions = functions
    
    def __getitem__(self, key: Any) -> Any:
        """访问包中的函数"""
        # 处理EW_String对象，转换为Python字符串
        if hasattr(key, 'value'):
            key_str = str(key.value)
        else:
            key_str = str(key)
        
        if key_str in self.functions:
            return self.functions[key_str]
        raise KeyError(f'Function {key_str} not found in package {self.name}')
    
    def __repr__(self) -> str:
        """返回包的字符串表示"""
        return f'<package {self.name} at {hex(id(self))}>'

# 全局包注册表
packages: Dict[str, EW_Package] = {}

# 包搜索路径
package_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pack'),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'includes')
]

def load_package_from_file(file_path: str) -> EW_Package:
    """从文件加载包"""
    # 读取文件内容，解析包名
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析包名（第一行注释）
    lines = content.split('\n')
    package_name = None
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            # 提取包名（去掉#和空格）
            package_name = line[1:].strip()
            break
    
    if not package_name:
        # 如果没有找到包名，使用文件名（去掉.py后缀，去掉EW_前缀）
        filename = os.path.basename(file_path).replace('.py', '')
        if filename.startswith('EW_'):
            package_name = filename[3:]
        else:
            package_name = filename
    
    # 执行模块，获取packall字典
    module_globals = {
        '__file__': file_path,
        '__name__': f'package.{package_name}'
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            exec(f.read(), module_globals)
    except Exception as e:
        raise_err(EW_RUNTIME_ERROR, f'Error loading package {package_name}: {e}')
        return None
    
    # 获取packall字典
    packall = module_globals.get('packall', {})
    
    # 创建并注册包
    package = EW_Package(package_name, packall)
    packages[package_name] = package
    
    return package

def auto_load_all_packages() -> None:
    """自动加载所有包搜索路径下的所有包，根据文件第一行注释提取包名"""
    for path in [os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pack')]:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.py'):
                    file_path = os.path.join(path, file)
                    load_package_from_file(file_path)

def load_package(package_name: str) -> EW_Package:
    """加载指定名称的包"""
    # 检查包是否已加载
    if package_name in packages:
        return packages[package_name]
    
    # 搜索包文件
    for path in package_paths:
        file_path = os.path.join(path, f'{package_name}.py')
        if os.path.exists(file_path):
            return load_package_from_file(file_path)
    
    raise_err(EW_RUNTIME_ERROR, f'Package {package_name} not found')
    return None

def import_package(package_name: str, env: 'Env') -> EW_Package:
    """导入包到指定环境"""
    package = load_package(package_name)
    if package:
        env[package_name] = package
    return package