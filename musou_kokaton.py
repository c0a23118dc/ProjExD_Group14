import math
import os
import random
import sys
import time
import pygame as pg


WIDTH, HEIGHT = 1600, 900  # ゲームウィンドウの幅，高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct:pg.Rect) -> tuple[bool, bool]:
    """
    Rectの画面内外判定用の関数
    引数：こうかとんRect，または，爆弾Rect，またはビームRect
    戻り値：横方向判定結果，縦方向判定結果（True：画面内／False：画面外）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:  # 横方向のはみ出し判定
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.state = "normal"
        self.hyper_life = 0
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        
        
            
    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
            if key_lst[pg.K_LSHIFT]:
                self.speed = 20
            else:
                self.speed = 10
                

            
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
        if self.hyper_life < 0:
            self.state = "normal"
        screen.blit(self.image, self.rect)
        
            
        
class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy, bird: Bird,  mode:str):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        if mode == "emy":
            rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
            self.image = pg.Surface((2*rad, 2*rad))
            color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
            pg.draw.circle(self.image, color, (rad, rad), rad)
            self.image.set_colorkey((0, 0, 0))
            self.rect = self.image.get_rect()
            self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
            self.rect.centerx = emy.rect.centerx
            self.rect.centery = emy.rect.centery+emy.rect.height/2
            self.speed = 6
            self.hp = 1  # HPの追加
            
        elif mode == "boss":
            self.image = pg.image.load(f"fig/fireball.png")
            self.image = pg.transform.scale(self.image, (130, 130))
            self.rect = self.image.get_rect()
            self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
            self.rect.centerx = emy.rect.centerx
            self.rect.centery = emy.rect.centery
            self.speed = 6
            self.hp = 5  # HPの追加

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """

        
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center =WIDTH, random.randint(0, HEIGHT)
        self.vx = +6
        self.bound = random.randint(WIDTH/2,WIDTH) # 停止位置
        self.state = "LEFT"  # 進行状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル
        self.hp = 1  # HPの追加

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centerx < self.bound:
            self.vx = 0
            self.state = "stop"
        self.rect.centery += self.vy
        


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 100
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class life_gage(pg.sprite.Sprite):
    """
    ライフゲージの作成  
    rectを用いてHPバーを作成し被弾するにつれてHPバーが減るようにする
    """

    def __init__(self,screen):
        self.colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0)] #ライフゲージの減少に伴って色の変化をさせる
        self.screen = screen

        # hpバーの幅・高さ
        self.hp_width = 300 # + 6
        self.hp_height = 40  #+ 6

        # HPバーを表示させたい位置
        self.hp_x = 160
        self.hp_y = 800

        self.hp = 100 #HPの基準

        self.HP_bar = pg.Surface((self.hp_width,self.hp_height)) #HPバーの土台作り
        self.HP_back = pg.Surface((self.hp_width +6,self.hp_height+6)) #HPバーの枠兼減少の値がわかりやすいようにする
        pg.draw.rect(self.HP_back, (0, 0, 0), (0,0,self.hp_width,self.hp_height)) #HPバーの枠作成
        pg.draw.rect(self.HP_bar, self.colors[1], (0,0,self.hp_width,self.hp_height)) #HPバー（緑色)の作成
        self.rect = self.HP_bar.get_rect()
        self.rect_back = self.HP_back.get_rect()
        
        self.rect.centerx = self.hp_x
        self.rect.centery = self.hp_y

        self.rect_back.center = (self.hp_x, self.hp_y)

        self.screen.blit(self.HP_back, self.rect_back)
        self.screen.blit(self.HP_bar, self.rect)


    def update(self,screen):
        # pg.draw.rect("(0,0)~(hp,10)まで表示")
        self.HP_bar = pg.Surface((300,self.hp_height))
        if self.hp <= 30: #HPが30以下の時表示を赤色にする
            pg.draw.rect(self.HP_bar, self.colors[0], (0,0,self.hp_width,self.hp_height))
        elif self.hp <= 60: #HPが60以下の時表示を黄色にする
            pg.draw.rect(self.HP_bar, self.colors[2], (0,0,self.hp_width,self.hp_height))
        else: #それ以外時表示を赤色にする
            pg.draw.rect(self.HP_bar, self.colors[1], (0,0,self.hp_width,self.hp_height))
        self.rect = self.HP_bar.get_rect()
        self.rect.centerx = self.hp_x
        self.rect.centery = self.hp_y
        screen.blit(self.HP_back, self.rect_back) #画面に反映
        screen.blit(self.HP_bar, self.rect) #画面に反映

    def dameges(self, damege):
        self.damege = damege
        self.damege*=3 #303行で300としているため100に割合をあわせるため
        self.hp_width -= self.damege

        print(damege, self.damege, self.hp_width) #ちゃんと実行されてHPが減っているかの確認
        self.hp -= damege

            

class Shield(pg.sprite.Sprite):
    """
    SPを3消費してこうかとんを守る防御壁を出現させるクラス
    Caps lock押下で出現
    """

    def __init__(self, bird : Bird, life):
        super().__init__()
        self.life = life
        self.image = pg.Surface((20, bird.rect.height*2))
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, 20, bird.rect.height*2))

        vx, vy = bird.dire
        deg = math.degrees(math.atan2(-vy, vx))
        self.image = pg.transform.rotozoom(self.image, deg, 1.0)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + bird.rect.width * vx
        self.rect.centery = bird.rect.centery + bird.rect.height * vy


    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()


class Gravity(pg.sprite.Sprite):
    """
    画面全体を覆う重力場を発生させる
    """
    def __init__(self, life):
        super().__init__()
        self.image = pg.Surface((1600,900))
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, 1600,900))
        self.image.set_alpha(200)
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH/2, HEIGHT/2) 
        self.life = life  # 発動時間

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()



    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()    

        
class EMP(pg.sprite.Sprite):
    def __init__(self, Enemy, Bomb, Surface): #敵機、爆弾、surfaceを与えている
        for emy in Enemy:
            emy.interval = math.inf
            emy.image = pg.transform.laplacian(emy.image)
            emy.image.set_colorkey((0, 0, 0))
        
        for bomb in Bomb:
            bomb.speed /= 2  

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()
            
           
class change_Boss():
    """
    １キーを押したときにボス戦警告のポップアップ表示
    Yesを押したときボス戦開始エフェクト+背景切り替え
    """
    def __init__(self, screen):
        self.screen = screen
        self.rct = pg.Surface((800, 450))  # Surfaceを生成
        pg.draw.rect(self.rct, (128, 128, 128), (0, 0, 800, 450))  # 灰色の矩形を生成
        # screen.blit(self.rct, (WIDTH/2, WIDTH/2))
        # time.sleep(1)
        # self.bg_img = pg.image.load(f"fig/aozora.jpg")  # ボス戦の画像読み込み
        # self.bg_img = pg.transform.scale(self.bg_img, (WIDTH, HEIGHT))  # ボス戦の背景画像サイズを調整
        
        self.font = pg.font.Font(None, 130)  # 文字の大きさ
        
        # 文字色の設定
        self.color = (255, 255, 255)
        self.color_red = (255, 0, 0)
        
        self.Yes = self.font.render("Yes", 0, self.color)
        self.No = self.font.render("No", 0, self.color)
        self.Ready = self.font.render("Are you ready ?", 0, self.color_red)
        
        # 透明度を設定
        self.rct.set_alpha(200)
        self.Yes.set_alpha(200)
        self.No.set_alpha(200)
        self.Ready.set_alpha(200)
        
        # 形の値を取得
        self.rect = self.Yes.get_rect()
        self.rect2 = self.No.get_rect()
        self.rect3 = self.Ready.get_rect()
        
        self.rect.center = 600, 600  # "Yes"の位置設定
        self.rect2.center = 1000, 600  # "No"の位置設定
        self.rect3.center = 800, 400   # "Are you ready?"の位置設定
        
        self.change = True  # ポップアップが表示されている状態に設定 (True : 表示, False: 非表示)

    def update(self, screen:pg.Surface):
        screen.blit(self.rct, (400, 300))  # Surfaceの描画、座標設定
        screen.blit(self.Yes, self.rect)  # Yesの描画
        screen.blit(self.No, self.rect2)  # Noの描画
        screen.blit(self.Ready, self.rect3)  # Are you ready?の描画
        
    def fade_in_out(self):
        fade_surface = pg.Surface((WIDTH, HEIGHT))
        fade_surface.fill((0, 0, 0))
        for i in range(0, 256, 5):  # フェードイン
            fade_surface.set_alpha(i)
            self.screen.blit(fade_surface, (0, 0))
            pg.display.flip()
            pg.time.delay(30)
        
        # self.screen.blit(self.bg_img, (0, 0))  # 背景画像を描画
        # pg.display.flip()
        # time.sleep(5)  # 背景画像を３秒間表示
            
            


class Powerup:
    """
    攻撃力の概念の追加
    打ち落とした爆弾が赤色だと攻撃力＋1
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 1
        self.image = self.font.render(f"Power: {self.value}", 0, self.color)  # 画面に攻撃力の数値を追加
        self.rect = self.image.get_rect()
        self.rect.center = 87, HEIGHT-100

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Power: {self.value}", 0, self.color)  # 数値を更新
        screen.blit(self.image, self.rect)


class Skillpoint:
    """
    スキルポイントの概念の追加
    打ち落とした爆弾が青色だとSP＋1
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 1
        self.image = self.font.render(f"SP: {self.value}", 0, self.color)  # 画面にスキルポイントの数値を追加
        self.rect = self.image.get_rect()
        self.rect.center = 58, HEIGHT-150

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"SP: {self.value}", 0, self.color)  # 数値を追加
        screen.blit(self.image, self.rect)


class Boss(pg.sprite.Sprite):
    def __init__(self, ):
        super().__init__()
        self.boss_flag = False
        self.image = pg.image.load(f"fig/last.png") #ボス画像の読み込み
        self.image = pg.transform.scale(self.image, (WIDTH/3, HEIGHT*(6/10))) #画像の大きさ調整
        self.rect = self.image.get_rect() #座標の取得
        self.rect.center = (WIDTH*(17/20), HEIGHT/2) #座標の指定
        self.B_HP = 100 #ボスのHP

    def update(self, M_life, score: Score):
        self.B_HP -= M_life
        print(self.B_HP)
        if self.B_HP <= 0:
            score.value += 200
            self.boss_flag = False
            self.kill()


def main():
    pg.display.set_caption("こうかとん伝説（仮）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    # bg_img2 = pg.image.load(f"fig/aozora.jpg")  # ボス戦の背景画像
    # bg_img2 = pg.transform.scale(bg_img2, (WIDTH, HEIGHT))  # ボス戦の背景画像サイズを調整
   
    # wait = WebDriverWait(driver=driver, timeout=60)
    score = Score()
    score.value = 99999  # 実行確認のために仮置き、後で消す
    power = Powerup()
    sp = Skillpoint()
    sp.value = 99999  # 実行確認のために仮置き、後で消す
    changeBoss = None  # 初期状態を設定
    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()
    gravity = pg.sprite.Group()
    bosses = pg.sprite.Group()
    boss = Boss()
    hp = life_gage(screen)
    #スライド
    bg_img2 = pg.transform.flip(bg_img,True,False) 
    kk_img = pg.transform.flip(bg_img,True,False)
    kk_rct = kk_img.get_rect()
    tmr = 0
    clock = pg.time.Clock()
    
    while True:
        x=0
        y=0
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_1 and (score.value >= 300):  # 1キーを押したときポップアップを表示
                changeBoss = change_Boss(screen) # クラス呼び出し
                score.value -= 100
                boss.boss_flag = True
                bosses.add(boss)
            if event.type == pg.MOUSEBUTTONDOWN:
                if changeBoss.rect.collidepoint(event.pos):
                    changeBoss.fade_in_out()
                    bg_img = pg.image.load(f"fig/aozora.jpg")
                    changeBoss = None  # ポップアップを閉じる
                elif changeBoss.rect2.collidepoint(event.pos):
                    changeBoss = None  # ポップアップを閉じる
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and (sp.value >= 5):  # 右シフトキーを押したときかつスキルポイントが5以上のとき
                bird.hyper_life = 500
                sp.value -= 5  # 消費SP
                bird.state = "hyper"  
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and sp.value >= 10:  # エンター押したときかつスキルポイントが10以上のとき
                gravity.add(Gravity(400))
                sp.value -= 10  # 消費SP
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                if sp.value > 8:
                    EMP(emys, bombs, screen)
                    sp.value -= 8  # 消費SP
            if event.type == pg.KEYDOWN and event.key == pg.K_w and sp.value >= 3 and len(shields) == 0:# SHIFTを押してからCaps lockを押す
                sp.value -= 3  # 消費SP
                shields.add(Shield(bird, 400))
                print(len(shields))
        screen.blit(bg_img, [0, 0])
        
        #スライド
        kk_rct.move_ip((x-1,y))

        x=tmr%3200
        screen.blit(bg_img, [-x, 0])
        screen.blit(bg_img2,[-x+1600,0])
        screen.blit(bg_img, [-x+3200,0])
        screen.blit(bg_img2,[-x+4800,0])

        screen.blit(kk_img,kk_rct)

        if boss.boss_flag == True:
            if tmr%30 == 0:
                bombs.add(Bomb(boss, bird, "boss"))

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird, "emy"))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            emy.hp -= power.value  # 敵のHPを自分の攻撃力分だけ削る
            if emy.hp <= 0:  # 敵のHPが0以下の時
                exps.add(Explosion(emy, 100))  # 爆発エフェクト
                score.value += 10  # 10点アップ
                bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            bomb.hp -= power.value  # 爆弾の耐久力を自分の攻撃力分だけ削る
            if bomb.hp <= 0:  # 爆弾の耐久力が0以下の時
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ
            if bomb.color == (255, 0, 0):  # 敵の爆弾の色が赤色のとき
                power.value += 1  # 攻撃力アップ
            if bomb.color == (0, 0, 255):  # 敵の爆弾の色が青色のとき
                sp.value += 1  # スキルポイントアップ
            """
            HPのクラスが追加されたら追加する
            今回はマージできないので追加しない
            """    
            #if bomb.color == (0, 255, 0):
            #    hp.value += 1  # HP回復

        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bird.state == "hyper":
                exps.add(Explosion(bomb, 50))
                score.value += 1
            if bird.state == "normal":
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)

                # ダメージ判定
                hp.dameges(10) #ダメージの割合、今回は敵の攻撃をくらったら10分の1ずつHPが減っていくようにする
                # pg.display.update()
                # time.sleep(2)
                # time.sleep(1)
                if hp.hp <= 0: #HPがなくなったらゲームオーバー
                    return
        
        # for ---------------------------------- 
            # if bossと当たったら チームメンバーがボスを作ったとき用

        for bomb in pg.sprite.groupcollide(bombs, gravity, True, False).keys():
            bomb.hp -= power.value  # 爆弾の耐久力を自分の攻撃力分だけ削る
            if bomb.hp <= 0:  # 爆弾の耐久力が0以下の時
                exps.add(Explosion(bomb, 50))
                score.value += 1
        
        for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():
            emy.hp -= power.value  # 敵のHPを自分の攻撃力分だけ削る
            if emy.hp <= 0:  # 敵のHPが0以下の時
                exps.add(Explosion(emy, 100))
                score.value += 10
                bird.change_img(6, screen)  # こうかとん喜びエフェクト


        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1
        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        for beam in pg.sprite.groupcollide(beams, bosses, True, False).keys(): #ボスとビームの衝突判定、爆発エフェクト
            exps.add(Explosion(beam, 50))
            bosses.update(10, score)        
        hp.update(screen)
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bosses.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        gravity.update()
        gravity.draw(screen)
        score.update(screen)
        shields.update()
        shields.draw(screen)
        power.update(screen)
        sp.update(screen)
        if changeBoss is not None:
            changeBoss.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
