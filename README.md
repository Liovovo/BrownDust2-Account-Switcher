# Browndust2 Account Switcher

Quickly switch between multiple Brown Dust 2 accounts on PC.

![Screenshot](bd2_img.png)

## Download

Download the latest executable from [Releases](https://github.com/Liovovo/BrownDust2-Account-Switcher/releases)

Or run from source:
```bash
pip install -r requirements.txt
python browndust2_account_switcher.py
```

## Important

- `accounts.json` contains sensitive data - **DO NOT SHARE**

## Disclaimer

This tool is provided "as is" without warranty. Use at your own risk. The developers are not responsible for any account issues, data loss, or violations of game terms of service that may result from using this tool.

## License

MIT


## 中文使用教程

1. 在游戏内登录账号A后，退出游戏，在账号切换器点击“另存当前账号”并自定义账号备注名称。
2. 在账号切换器点击“登出当前账号”后，启动游戏登录账号B，退出游戏，在账号切换器点击“另存当前账号”并自定义账号备注名称。

## 中文注意事项

- 经测试，可能偶现切换账号后游戏内提示API错误的情况，需要重新登录，并右键-覆盖账号。
- token每经12小时左右就会更新，在当前登录一栏点击刷新按钮即可看到当前登录账号的token时间。token更新后，点击“刷新Token”即可自动将当前登录账号token覆盖原保存的账号上。
- 工具会在运行目录下创建`accounts.json`，此文件包含保存的所有账号信息，**请勿共享**。

## 中文示例说明

- **当前登录**：当前游戏登录的账号信息。分别为：账号ID（非游戏内UID）或已保存的自定义名称、登录方式、注册地区、注册时间、Token时间。
- **账号列表**：已保存的账号列表。双击可加载并将此账号信息覆盖至注册表，右键可进行单独操作。
- **刷新Token**：将当前游戏登录的账号信息更新到已保存列表。见中文注意事项。
- **另存当前账号**：将当前游戏登录的账号信息另存为一个新的信息到已保存列表。
- **登出当前帐号**：将当前游戏登录的账号退出。
