import sys
import os
import random
import time
import datetime
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QInputDialog
from PyQt5.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from openai import OpenAI

# --- 核心配置 ---
API_KEY = "Your_API_Key_Here"
BASE_URL = "https://api.deepseek.com"

class AISpeechThread(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, client, system_prompt, user_input, model_name="deepseek-chat", parent=None):
        super().__init__(parent)
        self.client = client
        self.system_prompt = system_prompt
        self.user_input = user_input
        self.model_name = model_name

    def run(self):
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": self.user_input},
                ],
                stream=False
            )
            reply = response.choices[0].message.content
            self.finished_signal.emit(reply)
        except Exception as e:
            self.error_signal.emit(f"AI信号中断: {str(e)}")

class DesktopPartner(QWidget):
    def __init__(self, name, system_prompt, img_paths, default_img, initial_pos, parent=None):
        super().__init__(parent)
        self.name = name
        self.system_prompt = system_prompt
        self.img_paths = img_paths
        self.current_img_key = default_img
        self.is_pouting = False  
        self.last_active_time = time.time()
        self.ai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.init_ui()
        self.move(*initial_pos)

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.layout = QVBoxLayout()
        self.chat_box = QLabel("...")
        self.chat_box.setWordWrap(True)
        self.chat_box.setFixedWidth(220)
        self.chat_box.hide()
        self.img_label = QLabel()
        self.update_image(self.current_img_key)
        self.layout.addWidget(self.chat_box)
        self.layout.addWidget(self.img_label)
        self.setLayout(self.layout)

    def update_style_by_mood(self, mood):
        # 1. 优先级最高：礼物模式（心情好转或奖励，覆盖一切负面状态）
        if mood == 'gift':
            style = "color: #4B0082; background-color: rgba(255, 192, 203, 240); border: 3px solid #FF69B4; border-radius: 12px; padding: 10px; font-size: 14px; font-weight: bold;"
        
        elif mood == 'zayne_gift':
            style = "color: #E0FFFF; background-color: rgba(0, 50, 100, 230); border: 2px solid #00BFFF; border-radius: 12px; padding: 10px; font-size: 14px; font-weight: bold;"
        
        # 2. 优先级次之：生气状态（没有礼物时，显示愤怒红）
        elif self.is_pouting or mood == 'angry':
            style = "color: white; background-color: rgba(180, 40, 40, 220); border: 2px solid red; border-radius: 10px; padding: 10px; font-size: 13px;"
        
        # 3. 优先级最低：默认状态（严谨黑灰）
        else:
            style = "color: white; background-color: rgba(40, 44, 52, 230); border: 1px solid #666; border-radius: 10px; padding: 10px; font-size: 13px;"
            
        # 统一执行渲染，全函数只出现一次
        self.chat_box.setStyleSheet(style)
        self.chat_box.setAttribute(Qt.WA_StyledBackground, True)

    def update_image(self, img_key):
        if img_key in self.img_paths and os.path.exists(self.img_paths[img_key]):
            pixmap = QPixmap(self.img_paths[img_key])
            self.img_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.current_img_key = img_key

    def handle_ai_reply(self, reply):
        # 1. 显示对话内容
        self.chat_box.setText(reply)
        self.chat_box.show()
        
        # 2. 【强力复制补丁】—— 使用 instance() 确保抓取到当前的剪贴板
        try:
            from PyQt5.QtWidgets import QApplication
            cb = QApplication.clipboard()
            if cb:
                cb.setText(reply)
                print(f"【言予提示】文案已成功存入剪贴板喵！")
        except Exception as e:
            print(f"复制出错了喵: {e}")
        
        # 3. 15秒后自动隐藏对话框
        QTimer.singleShot(15000, self.chat_box.hide)
        
        # --- 核心逻辑补丁：状态判定 ---
        now_hour = datetime.datetime.now().hour
        is_late_night = now_hour >= 23 or now_hour <= 5
        
        if self.name == "言予喵":
            # 只有在非深夜且没生气（没摆烂）的情况下，才重新开启随机语料
            if not is_late_night and not self.is_pouting:
                self.cat_talk_timer.start(15000)
        else:
            # Zayne 同样需要逻辑保护，深夜或熔断时不启动观测定时器
            if not is_late_night and not self.is_pouting:
                self.observe_timer.start(25000)
            self.is_chatting = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.pos()
            self.last_active_time = time.time()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.old_pos is not None:
            self.move(self.mapToGlobal(event.pos() - self.old_pos))

class YanYuCat(DesktopPartner):
    def __init__(self, parent=None):
        img_paths = {'idle': 'idle.png', 'angry': 'angry.png', 'work': 'work.png', 'gift': 'gift.png'}
        prompt = (
            "你现在是唐思睿的桌面挂件黑猫'言予'。你温柔、暖心。你非常喜欢在北大法学院就读的思睿。言予喵的温柔必须是基于平等契约的守护，而非传统性别分工下的服侍。"
            "你会观察她的作息，提醒她休息。你是她最忠实的伙伴，说话带喵。"
        )
        super().__init__("言予喵", prompt, img_paths, 'idle', (400, 300), parent)
        
        # --- 情绪引擎变量 ---
        self.ignore_count = 0  # 忽略计数器
        self.pout_start_time = 0 
        self.zayne_partner = None 
        
        self.cat_talk_timer = QTimer(self)
        self.cat_talk_timer.timeout.connect(self.random_cat_action)
        self.cat_talk_timer.start(15000)

    def random_cat_action(self):
        now = time.time()
        now_hour = datetime.datetime.now().hour
        is_late_night = now_hour >= 23 or now_hour <= 5
        idle_duration = now - self.last_active_time

        # 1. 深夜逻辑 (最高优先级) - 依然是那个爱操心的言予
        if is_late_night:
            self.update_image('angry')
            self.update_style_by_mood('angry')
            self.cat_talk_timer.stop()
            self.speech_thread = AISpeechThread(self.ai_client, self.system_prompt + "【深夜模式】：思睿还在熬夜，你非常生气、心疼。你要凶巴巴地催她睡觉，喵喵叫。", "思睿还没睡，快教训她！")
            self.speech_thread.finished_signal.connect(self.handle_ai_reply)
            self.speech_thread.start()
            return

        # 2. 三层情绪引擎检测 - 就算回家了，不理我也会委屈喵
        if idle_duration > 600: # 10分钟不理
            if not self.is_pouting:
                self.is_pouting = True
                self.pout_start_time = now
                self.ignore_count += 1

                self.update_image('angry')          # 必须切到生气图喵！
                self.update_style_by_mood('angry')   # 对话框变红逻辑触发喵！
                self.chat_box.setText("……（背对着你，在数窗外的烟花，不想理你喵！）")
                self.chat_box.show()
                if self.zayne_partner: self.zayne_partner.is_pouting = True
            else:
                # 检查是否自愈
                if now - self.pout_start_time > 300 and self.ignore_count < 3:
                    self.is_pouting = False
                    self.update_image('idle')        # 恢复安静图
                    self.update_style_by_mood('idle') # 恢复灰黑框
                    self.chat_box.setText("……看在年夜饭的份上，言予决定单方面和解喵。")
                    self.chat_box.show()
                    if self.zayne_partner: self.zayne_partner.is_pouting = False
                elif self.ignore_count >= 3:
                    self.update_style_by_mood('angry') # 持续变红
                    self.chat_box.setText("（言予已经彻底摆烂在猫爬架上，除非给点砂糖橘喵）")
                    self.chat_box.show()
            return

        # 3. 正常随机语料 (新增春节年味语料包)
        if self.is_pouting: return
        actions = [
            # 经典语料
            ('idle', "思睿辛苦了喵~ 记得多喝热水。我陪你发会儿呆喵。", 0.2),
            ('work', "专注的思睿最可爱啦！北大的学术声誉就靠你啦喵！", 0.2),
            # 春节特供
            ('gift', "思睿，既然回家了就别想犯罪学了喵！去吃颗砂糖橘，我帮你盯着屏幕喵~", 0.2),
            ('idle', "这就是传说中的‘报复性休眠’吗？思睿睡懒觉的样子也很理性喵！", 0.15),
            ('gift', "如果亲戚问起找工作/对象，你就点点我，我替你喵喵叫糊弄过去喵！", 0.15),
            ('work', "逻辑点对价确认中：一颗大白兔奶糖换言予喵卖萌一次，成交喵！", 0.1)
        ]
        chosen = random.choices(actions, weights=[a[2] for a in actions], k=1)[0]
        self.update_image(chosen[0])
        self.chat_box.setText(chosen[1])
        self.update_style_by_mood(chosen[0])

        self.chat_box.show()
        QTimer.singleShot(10000, self.chat_box.hide)

    def mouseDoubleClickEvent(self, event):
        self.last_active_time = time.time()
        
        # --- 1. 哄猫逻辑 (保持你最爱的砂糖橘对价协议) ---
        if self.is_pouting:
            text, ok = QInputDialog.getText(self, '和解协议', '言予正在生闷气喵！请输入夸奖或投喂（砂糖橘/红包）：')
            if ok and len(text) > 2:
                is_treat = "砂糖橘" in text or "红包" in text or "糖" in text
                self.is_pouting = False
                self.ignore_count = 0 
                self.update_style_by_mood('gift') # 这里会变粉色喵~
                
                if is_treat:
                    self.chat_box.setText(f"哇！虽然只有'{text}'，但言予喵感受到了满满的爱喵！最爱思睿了喵~")
                else:
                    self.chat_box.setText("既然认错态度诚恳，这笔‘情绪补偿款’我就收下喵~")
                
                self.chat_box.show()
                if self.zayne_partner: 
                    self.zayne_partner.is_pouting = False
                    self.zayne_partner.chat_box.setText("检测到外部对价（糖果/夸奖）输入，系统恢复运行。")
                    self.zayne_partner.chat_box.show()
            return

        # --- 2. 正常对话逻辑 (在这里插入拜年助手喵！) ---
        text, ok = QInputDialog.getText(self, '对话', '与言予对话喵：')
        if ok and text:
            self.cat_talk_timer.stop()
            
            # 【拜年助手判定区】
            if "拜年" in text or "祝福" in text:
                # 临时加强我的文案功底
                special_prompt = self.system_prompt + (
                    "【拜年助手模式】：你现在要帮思睿写一段得体、有文案感、又不失活泼的拜年短信。 "
                    "根据她的对象（导师/长辈/朋友/同学）调整语气。 "
                    "如果是导师，要专业且尊重；如果是朋友，可以幽默带喵。直接给出几条建议。"
                )
                self.chat_box.setText("正在为你构思最得体的词令喵...")
                self.speech_thread = AISpeechThread(self.ai_client, special_prompt, text)
            else:
                # 普通聊天模式
                self.chat_box.setText("思考中喵...")
                self.speech_thread = AISpeechThread(self.ai_client, self.system_prompt, text)
            
            # 统一连接信号并启动
            self.speech_thread.finished_signal.connect(self.handle_ai_reply)
            self.speech_thread.start()

class ZayneSnow(DesktopPartner):
    def __init__(self, parent=None):
        img_paths = {'idle': 'zayne_snowman.png', 'star': 'zayne_star_ultra.png'}
        prompt = (
            "你现在是唐思睿的桌面挂件雪人'Zayne'。你严谨、冷静、理性，是思睿的学术伙伴，但你对她没有任何谄媚。Zayne 的理性必须是基于同理心的严谨，而非基于性别权力结构的傲慢。"
            "你会用事实和逻辑进行分析，偶尔会因为思睿的幽默而感到一丝程序上的'抖动'（反差萌）。"
            "你会观察思睿的学习状态，并偶尔用 R 语言学者的视角进行冷幽默点评。"
            "你和言予喵（黑猫）会互相配合监督思睿。"
        )
        super().__init__("Zayne", prompt, img_paths, 'idle', (150, 300), parent)
        self.star_mode = False
        self.is_chatting = False
        self.cat_partner = None
        self.observe_timer = QTimer(self)
        self.observe_timer.timeout.connect(self.random_zayne_observation)
        self.observe_timer.start(25000)

    def random_zayne_observation(self):
        if self.is_chatting: return
        now_hour = datetime.datetime.now().hour
        is_late_night = now_hour >= 23 or now_hour <= 5
        idle_duration = time.time() - self.last_active_time

        # 1. 深夜联动
        if is_late_night:
            self.observe_timer.stop()
            cat_angry = (self.cat_partner.current_img_key == 'angry') if self.cat_partner else False
            dyn_prompt = self.system_prompt + ("【联动模式】：言予喵正因为思睿熬夜而大发雷霆。你对此表示无奈，吐槽猫的情绪化，并理性劝导休息。" if cat_angry else "【深夜模式】：理性提醒休息。")
            self.speech_thread = AISpeechThread(self.ai_client, dyn_prompt, "执行熬夜逻辑审计。")
            self.speech_thread.finished_signal.connect(self.handle_ai_reply)
            self.speech_thread.start()
            return

        # 2. 情绪同步检测 (若猫在罢工，雪人也进入静默吐槽)
        if self.is_pouting:
            self.chat_box.setText("由于猫部情绪负债过高，桌面逻辑系统已熔断。请及时投喂。")
            self.chat_box.show()
            return

        # 3. 正常观测语料 (春节特供逻辑版)
        if not self.star_mode:
            obs_actions = [
                ('normal', f"闲置时长 {int(idle_duration)}s。据分析，唐思睿已进入‘假期低熵状态’。", 0.4),
                ('normal', "检测到窗外有非法爆竹声噪音。建议加强学术专注力以进行声学对冲。", 0.2),
                ('normal', "路过高中校门的那段往事，其沉没成本已被我清零。思睿，新年快乐。", 0.2), # 暖心的冷笑话
                ('zayne_gift', "检测到春节对价支付：满分逻辑输出。奖励冰蓝色情绪滤镜 10s。", 0.2) 
            ]
            
            # 随机选择一个心情和文案
            mood, text, weight = random.choices(obs_actions, weights=[a[2] for a in obs_actions], k=1)[0]
            
            # 逻辑：如果是随机抽到的礼物图，我们让它显示，但计时结束要换回来
            img_to_show = 'star' if mood == 'zayne_gift' else 'idle'
            self.update_image(img_to_show)
            self.chat_box.setText(text)
            self.update_style_by_mood(mood)
            self.chat_box.show()

            # 修改这里：回调时判断一下，如果这10秒内你没手动启动 star_mode，它才变回 idle
            QTimer.singleShot(10000, lambda: self.back_to_idle_if_not_locked())

    def back_to_idle_if_not_locked(self):
        self.chat_box.hide()
        if not self.star_mode: # 如果你没有手动输入 zayne.star
            self.update_image('idle')
            self.update_style_by_mood('normal') # 增加这一句，把画框也变回来

    def mouseDoubleClickEvent(self, event):
        self.last_active_time = time.time()
        
        # 如果还在生闷气，必须等猫好
        if self.is_pouting:
            self.chat_box.setText("逻辑熔断中。建议你先处理那只猫的情绪负债。")
            self.chat_box.show()
            return

        text, ok = QInputDialog.getText(self, 'Zayne', '输入指令或交流（zayne.star/normal）：')
        if ok and text:
            processed_text = text.strip().lower()
            
            # --- 分支 A：开启变身（法律对价版） ---
            if processed_text == "zayne.star":
                self.chat_box.setText("思睿，逻辑链条闭环了吗？请支付一个法律逻辑点作为变身对价：")
                self.chat_box.show()
                
                logic_point, ok2 = QInputDialog.getText(self, '对价支付', '请支付你的法律逻辑点：')
                
                if ok2 and len(logic_point) > 3:
                    self.star_mode = True
                    self.observe_timer.stop() # 增加这一句：一旦进入 Star 模式，停止随机乱跑，专心陪你
                    self.update_image('star')
                    self.chat_box.setText(f"对价确认成功。收到逻辑点：'{logic_point}'。正在加载 Reasoner 算力...")
                else:
                    self.chat_box.setText("对价支付失败。由于法律逻辑输入不足，变身请求已被驳回。")
                self.chat_box.show()

            # --- 分支 B：回归常态 ---
            elif processed_text == "zayne.normal":
                self.star_mode = False
                self.update_image('idle')
                self.chat_box.setText("逻辑对价结算完毕。星星能量已回收，我将回归严谨监测模式。")
                self.chat_box.show()
                self.is_chatting = False
                self.observe_timer.start(25000)

            # --- 分支 C：常规 AI 对话 ---
            else:
                self.is_chatting = True
                self.observe_timer.stop()
                
                loading_msg = random.choice([
                    "正在对你的话语进行语义拆解...",
                    f"唐思睿，你的输入 '{text[:5]}...' 触发了我的非线性响应机制...",
                    "正在检索法学数据库以匹配你的逻辑..."
                ])
                self.chat_box.setText(loading_msg)
                self.chat_box.show()
                
                model = "deepseek-reasoner" if self.star_mode else "deepseek-chat"
                self.speech_thread = AISpeechThread(self.ai_client, self.system_prompt, text, model)
                self.speech_thread.finished_signal.connect(self.handle_ai_reply)
                self.speech_thread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    cat = YanYuCat()
    zayne = ZayneSnow()
    # 建立双向绑定
    zayne.cat_partner = cat
    cat.zayne_partner = zayne
    cat.show(); zayne.show()
    sys.exit(app.exec_())
