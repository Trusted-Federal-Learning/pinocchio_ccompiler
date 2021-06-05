# pinocchio_ccompiler

将特定形式的C源码转换为算数电路，并生成调用libsnark进行验证的代码

基于 https://vc.codeplex.com 项目中的编译器进行开发

https://www.microsoft.com/en-us/research/publication/pinocchio-nearly-practical-verifiable-computation/

安装运行环境

python2

`python -m pip install -r .\requirements.txt`

编译

`bash src/compile.sh cfile`

执行电路

`bash src/arith_exec.sh arith arith_input`

