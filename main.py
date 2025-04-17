from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import At, Plain, Image
from astrbot.api import AstrBotConfig
import json
import logging
import os
import random

@register(
    "astrbot_plugin_enter_group", 
    "和泉智宏", 
    "进群欢迎插件，支持自定义欢迎消息和群聊白名单，支持图片欢迎", 
    "1.1",
    "https://github.com/0d00-Ciallo-0721/astrbot_plugin_enter_group"
)
class GroupWelcomePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.logger = logging.getLogger("GroupWelcomePlugin")
        
        # 初始化配置
        self.enabled_groups = self.config.get("enabled_groups", [])
        self.welcome_message = self.config.get("welcome_message", "欢迎新成员加入群聊")
        self.enable_image = self.config.get("enable_image", True)
        self.image_folder = self.config.get("image_folder", "welcome_images")
        
        # 确保群组ID是字符串类型
        self.enabled_groups = [str(gid) for gid in self.enabled_groups]
        
        # 创建图片文件夹（如果不存在）
        self.image_folder_path = os.path.join(os.path.dirname(__file__), self.image_folder)
        if not os.path.exists(self.image_folder_path):
            os.makedirs(self.image_folder_path)
            self.logger.info(f"创建图片文件夹: {self.image_folder_path}")
        
        self.logger.info(f"插件已加载，启用群组: {self.enabled_groups}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_all_message(self, event: AstrMessageEvent):
        try:
            raw_message = event.message_obj.raw_message
            
            # 检查是否为群成员增加事件
            if (raw_message.get('post_type') == 'notice' and 
                raw_message.get('notice_type') == 'group_increase'):
                
                group_id = str(raw_message.get('group_id'))
                user_id = str(raw_message.get('user_id'))
                
                self.logger.info(f"检测到新成员加入: 群 {group_id}, 用户 {user_id}")
                
                # 检查是否在启用群组中
                if group_id in self.enabled_groups:
                    # 创建消息链
                    message_chain = [
                        At(qq=user_id),
                        Plain(" " + self.welcome_message)
                    ]
                    
                    # 如果启用了图片欢迎，添加随机图片
                    if self.enable_image:
                        image_files = [f for f in os.listdir(self.image_folder_path) 
                                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                        
                        if image_files:  # 确保有图片可用
                            random_image = random.choice(image_files)
                            image_path = os.path.join(self.image_folder_path, random_image)
                            message_chain.append(Image.fromFileSystem(image_path))
                        else:
                            self.logger.warning(f"图片文件夹 {self.image_folder_path} 中没有图片")
                    
                    # 返回消息结果
                    yield event.chain_result(message_chain)
                    
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}", exc_info=True)

    @filter.command("welcome_enable")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def enable_group(self, event: AstrMessageEvent, group_id: str = None):
        """启用当前群聊的欢迎功能"""
        try:
            if not group_id:
                group_id = str(event.get_group_id())
                if not group_id:
                    yield event.plain_result("请在群聊中使用此命令或指定群号")
                    return
            
            if group_id not in self.enabled_groups:
                self.enabled_groups.append(group_id)
                self.config["enabled_groups"] = self.enabled_groups
                self.config.save_config()
                yield event.plain_result(f"已启用群 {group_id} 的欢迎功能")
            else:
                yield event.plain_result(f"群 {group_id} 的欢迎功能已经启用")
                
        except Exception as e:
            self.logger.error(f"启用群聊时出错: {e}")
            yield event.plain_result("启用群聊时出错")

    @filter.command("welcome_disable")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def disable_group(self, event: AstrMessageEvent, group_id: str = None):
        """禁用当前群聊的欢迎功能"""
        try:
            if not group_id:
                group_id = str(event.get_group_id())
                if not group_id:
                    yield event.plain_result("请在群聊中使用此命令或指定群号")
                    return
            
            if group_id in self.enabled_groups:
                self.enabled_groups.remove(group_id)
                self.config["enabled_groups"] = self.enabled_groups
                self.config.save_config()
                yield event.plain_result(f"已禁用群 {group_id} 的欢迎功能")
            else:
                yield event.plain_result(f"群 {group_id} 的欢迎功能已经禁用")
                
        except Exception as e:
            self.logger.error(f"禁用群聊时出错: {e}")
            yield event.plain_result("禁用群聊时出错")

    @filter.command("welcome_set")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def set_welcome_message(self, event: AstrMessageEvent, *, message: str):
        """设置欢迎消息"""
        try:
            self.welcome_message = message
            self.config["welcome_message"] = message
            self.config.save_config()
            yield event.plain_result("欢迎消息已更新")
            
        except Exception as e:
            self.logger.error(f"设置欢迎消息时出错: {e}")
            yield event.plain_result("设置欢迎消息时出错")

    @filter.command("welcome_show")
    async def show_welcome_message(self, event: AstrMessageEvent):
        """显示当前欢迎消息"""
        yield event.plain_result(f"当前欢迎消息: {self.welcome_message}")

    @filter.command("welcome_image_enable")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def enable_image(self, event: AstrMessageEvent):
        """启用图片欢迎功能"""
        try:
            self.enable_image = True
            self.config["enable_image"] = True
            self.config.save_config()
            yield event.plain_result("图片欢迎功能已启用")
        except Exception as e:
            self.logger.error(f"启用图片欢迎功能时出错: {e}")
            yield event.plain_result("启用图片欢迎功能时出错")

    @filter.command("welcome_image_disable")
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def disable_image(self, event: AstrMessageEvent):
        """禁用图片欢迎功能"""
        try:
            self.enable_image = False
            self.config["enable_image"] = False
            self.config.save_config()
            yield event.plain_result("图片欢迎功能已禁用")
        except Exception as e:
            self.logger.error(f"禁用图片欢迎功能时出错: {e}")
            yield event.plain_result("禁用图片欢迎功能时出错")

    @filter.command("welcome_status")
    async def show_status(self, event: AstrMessageEvent):
        """显示插件状态"""
        status = f"欢迎插件状态:\n"
        status += f"启用群组: {', '.join(self.enabled_groups) or '无'}\n"
        status += f"欢迎消息: {self.welcome_message}\n"
        status += f"图片欢迎: {'启用' if self.enable_image else '禁用'}\n"
        status += f"图片文件夹: {self.image_folder_path}"
        
        # 获取欢迎图片数量
        try:
            image_count = len([f for f in os.listdir(self.image_folder_path) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))])
            status += f"\n可用图片数量: {image_count}"
        except:
            status += "\n可用图片数量: 无法获取"
            
        yield event.plain_result(status)

    async def terminate(self):
        """插件终止时保存配置"""
        self.config.save_config()
        self.logger.info("插件已卸载")
