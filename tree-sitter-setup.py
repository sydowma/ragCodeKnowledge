import os
import subprocess

# 确保目录存在
os.makedirs('build', exist_ok=True)

# 克隆 tree-sitter-java 仓库（如果还没有的话）
if not os.path.exists('tree-sitter-java'):
    subprocess.run(['git', 'clone', 'https://github.com/tree-sitter/tree-sitter-java.git'], check=True)

# 进入 tree-sitter-java 目录
os.chdir('tree-sitter-java')

# 编译语言库
subprocess.run(['cc', '-fPIC', '-c', 'src/parser.c', '-I./src'], check=True)
subprocess.run(['cc', '-fPIC', '-shared', 'parser.o', '-o', '../build/java.so'], check=True)

# 返回上一级目录
os.chdir('..')

print("Tree-sitter Java language support has been built successfully.")