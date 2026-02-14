#!/bin/bash
# 1. 切换到项目文件夹（只到文件夹这一层，别进图片！）
cd "/Users/tangsirui/Desktop/snow_cat system"

# 2. 杀死旧进程，防止重复启动
pkill -f monitors.py

# 3. 启动程序
# 提示：如果终端提示找不到 python3，可以换成具体路径
python3 monitors.py &

echo "【系统审计】：逻辑已重载，言予喵和 Zayne 重新就位喵！"