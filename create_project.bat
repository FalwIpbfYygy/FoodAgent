@echo off
chcp 65001 > nul
echo 开始创建smart_dian_can项目结构...

:: 创建根目录
md smart_dian_can

:: 创建各级目录
md smart_dian_can\api
md smart_dian_can\agent
md smart_dian_can\tools
md smart_dian_can\service
md smart_dian_can\prompt

:: 创建空文件
type nul > smart_dian_can\api\main.py
type nul > smart_dian_can\api\models.py
type nul > smart_dian_can\agent\mcp.py
type nul > smart_dian_can\agent\smart_agent.py
type nul > smart_dian_can\tools\amap_tool.py
type nul > smart_dian_can\tools\db_tool.py
type nul > smart_dian_can\tools\llm_tool.py
type nul > smart_dian_can\tools\pinecone_tool.py
type nul > smart_dian_can\service\diancan_service.py
type nul > smart_dian_can\prompt\general_inquiry.txt
type nul > smart_dian_can\prompt\menu_inquiry.txt
type nul > smart_dian_can\run.py
type nul > smart_dian_can\requirements.txt

echo 项目结构创建完成！
pause