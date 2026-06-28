import os
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from app_pages_framework import render_new_service_loop_pages

# 图片资源目录候选：项目根/img 与 src/img，均相对本文件定位，不依赖启动时的工作目录
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_IMG_DIRS = [
    os.path.join(os.path.dirname(_APP_DIR), "img"),  # <项目根>/img
    os.path.join(_APP_DIR, "img"),                   # src/img
]


def show_image(filename, caption=None):
    """安全显示图片：在候选目录中查找，找到则渲染，缺失则显示占位提示而非崩溃。

    filename 形如 "img/campus.png" 或 "campus.png"，仅取文件名做查找。
    """
    name = os.path.basename(filename)
    for d in _IMG_DIRS:
        path = os.path.join(d, name)
        if os.path.isfile(path):
            st.image(path, caption=caption, width="stretch")
            return
    st.info(f"📷 图片素材缺失：`{name}`（请将其放入项目根的 img/ 目录后刷新）")

# =========================
# 页面配置
# =========================
st.set_page_config(page_title="知药护身·护佑零艾 数字化PrEP健康管理平台", layout="wide")

# =========================
# 超级顶配PLUS版动态特效层：粒子+流星+光轨+扫描线+星座连线+鼠标爆炸+星云+边缘流光
# =========================
st.markdown("""
<div style="position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:-100; pointer-events:none; overflow:hidden;">
<canvas id="main-canvas" style="width:100%; height:100%;"></canvas>
</div>

<script>
const canvas = document.getElementById('main-canvas');
const ctx = canvas.getContext('2d');
let w, h;
let mouse = { x: null, y: null, radius: 180, clicked: false, rightClicked: false };

// 鼠标移动 + 左右键点击
window.addEventListener('mousemove', e => {
    mouse.x = e.x;
    mouse.y = e.y;
});
window.addEventListener('mousedown', e => { 
    if(e.button === 0) mouse.clicked = true;
    if(e.button === 2) mouse.rightClicked = true;
});
window.addEventListener('mouseup', e => { 
    mouse.clicked = false; 
    mouse.rightClicked = false;
});
window.addEventListener('contextmenu', e=>e.preventDefault());

// 窗口大小
function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
}
window.addEventListener('resize', resize);
resize();

// ===================== 1. 基础粒子（增强引力+拖影+星云粒子） =====================
class Particle {
    constructor(type="normal") {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.type = type;
        if(type === "star"){
            this.size = Math.random() * 1.5 + 0.2;
            this.speedX = Math.random() * 0.2 - 0.1;
            this.speedY = Math.random() * 0.2 - 0.1;
            this.opacity = Math.random() * 0.4 + 0.1;
            this.color = `rgba(180,220,255,${this.opacity})`;
        }else if(type === "glow"){
            this.size = Math.random() * 3 + 1;
            this.speedX = Math.random() * 0.4 - 0.2;
            this.speedY = Math.random() * 0.4 - 0.2;
            this.opacity = Math.random() * 0.6 + 0.2;
            this.color = `rgba(100,180,255,${this.opacity})`;
        }else if(type === "click"){
            this.size = Math.random() * 4 + 2;
            this.speedX = (Math.random() - 0.5) * 6;
            this.speedY = (Math.random() - 0.5) * 6;
            this.opacity = 1;
            this.color = `rgba(100, 180, 255, 1)`;
            this.life = 1;
        }else if(type === "nebula"){
            this.size = Math.random() * 8 + 4;
            this.speedX = Math.random() * 0.15 - 0.075;
            this.speedY = Math.random() * 0.15 - 0.075;
            this.opacity = Math.random() * 0.15 + 0.05;
            this.color = `rgba(130, 160, 255, ${this.opacity})`;
        }else{
            this.size = Math.random() * 2 + 0.5;
            this.speedX = Math.random() * 0.5 - 0.25;
            this.speedY = Math.random() * 0.5 - 0.25;
            this.opacity = Math.random() * 0.5 + 0.1;
            this.color = `rgba(77, 166, 255, ${this.opacity})`;
        }
    }
    update() {
        if(this.type === "click"){
            this.life -= 0.02;
            this.size *= 0.96;
            if(this.life <= 0) return;
        }
        this.x += this.speedX;
        this.y += this.speedY;
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if(dist < mouse.radius){
            const force = (mouse.radius - dist)/mouse.radius;
            this.x -= dx * force * 0.03;
            this.y -= dy * force * 0.03;
        }
        if(this.x <0||this.x>w) this.speedX*=-1;
        if(this.y <0||this.y>h) this.speedY*=-1;
    }
    draw() {
        if(this.type === "click" && this.life <=0) return;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI*2);
        ctx.fillStyle = this.color;
        ctx.fill();
    }
}

// ===================== 2. 流星（彩色渐变尾迹） =====================
class Meteor {
    constructor(){
        this.reset();
    }
    reset(){
        this.x = Math.random() * w;
        this.y = 0;
        this.speed = Math.random() * 8 + 4;
        this.length = Math.random() * 80 + 40;
        this.opacity = Math.random() * 0.6 + 0.2;
        this.hue = Math.random() * 60 + 160;
        this.color = `hsla(${this.hue}, 85%, 75%, ${this.opacity})`;
    }
    update(){
        this.y += this.speed;
        this.x += this.speed * 0.5;
        if(this.y > h || this.x > w) this.reset();
    }
    draw(){
        ctx.beginPath();
        ctx.moveTo(this.x, this.y);
        ctx.lineTo(this.x - this.length*0.5, this.y - this.length);
        ctx.strokeStyle = this.color;
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

// ===================== 3. 多层流动波纹 =====================
class WaveLine {
    constructor() {
        this.offset = Math.random() * 1000;
        this.speed = Math.random() * 0.008 + 0.003;
        this.amplitude = Math.random() * 40 + 20;
        this.yBase = Math.random() * h;
        this.opacity = Math.random() * 0.15 + 0.05;
    }
    draw(time) {
        ctx.beginPath();
        ctx.moveTo(0, this.yBase);
        for(let x=0;x<w;x+=5){
            const y = this.yBase + Math.sin(x*0.01 + time*this.speed + this.offset) * this.amplitude;
            ctx.lineTo(x, y);
        }
        ctx.strokeStyle = `rgba(100,180,255,${this.opacity})`;
        ctx.lineWidth = 1;
        ctx.stroke();
    }
}

// ===================== 4. 多线交错科技扫描线 =====================
class ScanLine {
    constructor(){
        this.y = 0;
        this.speed = 0.4;
        this.opacity = Math.random()*0.12+0.05;
    }
    update(){
        this.y += this.speed;
        if(this.y > h) this.y = 0;
    }
    draw(){
        ctx.beginPath();
        ctx.moveTo(0, this.y);
        ctx.lineTo(w, this.y);
        ctx.strokeStyle = `rgba(100, 180, 255, ${this.opacity})`;
        ctx.lineWidth = 3;
        ctx.stroke();
    }
}

// ===================== 5. 鼠标光迹拖尾 =====================
let trail = [];
function addTrail(x,y){
    trail.push({x,y,life:1});
    if(trail.length > 30) trail.shift();
}
function drawTrail(){
    for(let i=0;i<trail.length;i++){
        const t = trail[i];
        t.life *= 0.95;
        ctx.beginPath();
        ctx.arc(t.x, t.y, 6 * t.life, 0, Math.PI*2);
        ctx.fillStyle = `rgba(120, 190, 255, ${t.life * 0.3})`;
        ctx.fill();
    }
}

// ===================== 6. 粒子星座连线 =====================
function drawConnect(){
    for(let i=0;i<particles.length;i++){
        const p1 = particles[i];
        for(let j=i+1;j<particles.length;j++){
            const p2 = particles[j];
            const dx = p1.x - p2.x;
            const dy = p1.y - p2.y;
            const dist = Math.sqrt(dx*dx+dy*dy);
            if(dist < 120){
                ctx.beginPath();
                ctx.moveTo(p1.x,p1.y);
                ctx.lineTo(p2.x,p2.y);
                ctx.strokeStyle = `rgba(100,180,255,${0.15 - dist/800})`;
                ctx.lineWidth = 0.5;
                ctx.stroke();
            }
        }
    }
}

// ===================== 7. 屏幕边缘流光扫光 =====================
function drawEdgeGlow(time){
    const gradL = ctx.createLinearGradient(0,0,40,0);
    gradL.addColorStop(0,"rgba(100,180,255,0)");
    gradL.addColorStop(1,"rgba(100,180,255,0.2)");
    const gradR = ctx.createLinearGradient(w-40,0,w,0);
    gradR.addColorStop(0,"rgba(100,180,255,0.2)");
    gradR.addColorStop(1,"rgba(100,180,255,0)");
    ctx.fillStyle = gradL;
    ctx.fillRect(0,0,40,h);
    ctx.fillStyle = gradR;
    ctx.fillRect(w-40,0,40,h);
}

// 初始化所有效果
let particles = [];
let meteors = [];
let waveLines = [];
let scanLines = [];

for(let i=0;i<160;i++) particles.push(new Particle("normal"));
for(let i=0;i<80;i++) particles.push(new Particle("star"));
for(let i=0;i<60;i++) particles.push(new Particle("glow"));
for(let i=0;i<40;i++) particles.push(new Particle("nebula"));
for(let i=0;i<12;i++) meteors.push(new Meteor());
for(let i=0;i<12;i++) waveLines.push(new WaveLine());
for(let i=0;i<4;i++) scanLines.push(new ScanLine());

// 鼠标左右键爆炸
function clickExplode(){
    if(!mouse.clicked || !mouse.x) return;
    for(let i=0;i<12;i++){
        let p = new Particle("click");
        p.x = mouse.x;
        p.y = mouse.y;
        particles.push(p);
    }
    mouse.clicked = false;
}
function rightClickExplode(){
    if(!mouse.rightClicked || !mouse.x) return;
    for(let i=0;i<20;i++){
        let p = new Particle("click");
        p.x = mouse.x;
        p.y = mouse.y;
        p.speedX = (Math.random()-0.5)*8;
        p.speedY = (Math.random()-0.5)*8;
        particles.push(p);
    }
    mouse.rightClicked = false;
}

// 鼠标光晕
function drawMouseGlow(time){
    if(!mouse.x) return;
    const grad = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, mouse.radius);
    grad.addColorStop(0, "rgba(120,190,255,0.35)");
    grad.addColorStop(0.4, "rgba(100,170,255,0.15)");
    grad.addColorStop(1, "rgba(80,150,255,0)");
    ctx.beginPath();
    ctx.arc(mouse.x, mouse.y, mouse.radius, 0, Math.PI*2);
    ctx.fillStyle = grad;
    ctx.fill();
}

// 动画循环
let startTime = Date.now();
function animate(){
    const time = Date.now() - startTime;
    ctx.clearRect(0,0,w,h);

    // 边缘流光
    drawEdgeGlow(time);
    // 光迹
    if(mouse.x) addTrail(mouse.x, mouse.y);
    drawTrail();
    // 波纹
    waveLines.forEach(line=>line.draw(time));
    // 扫描线
    scanLines.forEach(s=>{s.update();s.draw();});
    // 流星
    meteors.forEach(m=>{m.update();m.draw();});
    // 粒子连线
    drawConnect();
    // 鼠标光晕
    drawMouseGlow(time);
    // 点击爆炸
    clickExplode();
    rightClickExplode();
    // 粒子
    particles.forEach(p=>{p.update();p.draw();});

    requestAnimationFrame(animate);
}
animate();
</script>
""", unsafe_allow_html=True)

# =========================
# 超级顶配PLUS版CSS：3D旋转+通电闪光+霓虹流动+点击冲击波+悬浮强化+新增大量高级动画
# =========================
st.markdown("""
<style>
/* ===== 全局底层背景 + 动态星云 + 页面入场动画 ===== */
body {
    background: radial-gradient(ellipse at 20% 50%, #0a0e27 0%, #020617 100%) !important;
    color: #e2e8f0 !important;
    overflow-x: hidden;
    animation: pageFadeIn 1.5s ease-out;
}
@keyframes pageFadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* 主内容容器强制上层显示 */
.block-container {
    padding-top: 2rem;
    position: relative !important;
    z-index: 10 !important;
}

/* ===== 主卡片：3D全息扫描 + 倾斜视差 + 霓虹旋转边框 + 通电流光 + 边角电弧 ===== */
.main-card {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 58, 138, 0.6));
    backdrop-filter: blur(25px);
    border: 1px solid rgba(77, 166, 255, 0.35);
    border-radius: 32px;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255,255,255,0.15), inset 0 0 30px rgba(67,97,238,0.15);
    padding: 40px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    transition: transform 0.4s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.4s;
    z-index: 1;
    transform-style: preserve-3d;
    animation: cardInnerGlowPulse 4s infinite alternate;
}
@keyframes cardInnerGlowPulse {
    0% { box-shadow: 0 8px 40px rgba(0,0,0,0.7), inset 0 0 20px rgba(67,97,238,0.1); }
    100% { box-shadow: 0 8px 40px rgba(0,0,0,0.7), inset 0 0 40px rgba(67,97,238,0.25); }
}
.main-card:hover {
    transform: translateY(-8px) rotateX(2deg) rotateY(-2deg) scale(1.01);
    box-shadow: 0 20px 60px rgba(67,97,238,0.5), inset 0 0 50px rgba(67,97,238,0.3);
}
.main-card::before {
    content: "";
    position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
    background: linear-gradient(45deg, 
        transparent 40%, 
        rgba(255,255,255,0.07) 45%, 
        rgba(255,255,255,0.2) 50%, 
        rgba(255,255,255,0.07) 55%, 
        transparent 60%);
    animation: scanRotate 6s linear infinite;
    pointer-events: none;
}
.main-card::after {
    content: "";
    position: absolute; inset: 0;
    border-radius: 32px;
    padding: 2px;
    background: linear-gradient(60deg, #60a5fa, #a78bfa, #f472b6, #60a5fa);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    animation: borderGlow 3s ease-in-out infinite alternate;
    pointer-events: none;
}
.main-card .corner-arc {
    position:absolute; width:80px;height:80px;
    border:2px solid rgba(100,180,255,0.4);
    animation: arcElectric 2s infinite alternate;
}
@keyframes arcElectric {
    0% { opacity:0.3; transform:scale(0.9); }
    100% { opacity:0.8; transform:scale(1.1); }
}

/* ===== 次级卡片：悬浮上浮 + 发光扩散 + 霓虹边框 + hover波纹 ===== */
.card {
    background: rgba(15, 23, 42, 0.65);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 22px;
    transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    z-index: 1;
}
.card::before {
    content: "";
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 50% 0%, rgba(255,255,255,0.08), transparent 70%);
    pointer-events: none;
}
.card::after {
    content:"";
    position:absolute; top:50%; left:50%; width:0;height:0;
    background:radial-gradient(circle,rgba(100,180,255,0.2),transparent);
    border-radius:50%;
    transform:translate(-50%,-50%);
    transition:width 0.6s ease,height 0.6s ease;
}
.card:hover::after { width:300%; height:300%; }
.card:hover {
    transform: translateY(-12px) scale(1.03);
    box-shadow: 0 30px 50px rgba(56,189,248,0.35), inset 0 1px 0 rgba(255,255,255,0.25);
    border-color: rgba(77, 166, 255, 0.6);
}

/* ===== 高亮卡片：强呼吸脉冲 ===== */
.highlight-card {
    background: linear-gradient(135deg, rgba(67, 97, 238, 0.25), rgba(58, 12, 163, 0.25));
    border: 1px solid rgba(77, 166, 255, 0.45);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
    position: relative;
    animation: glowPulse 2s ease-in-out infinite alternate;
    z-index: 1;
}

/* ===== 统计卡片：悬浮上浮 + 数字流光 ===== */
.icon-stat-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    padding: 24px;
    text-align: center;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
    z-index: 1;
}
.icon-stat-card:hover {
    transform: translateY(-8px);
    border-color: rgba(77, 166, 255, 0.5);
    box-shadow: 0 20px 40px rgba(56,189,248,0.25);
}
.icon-stat-number {
    font-size: 42px;
    font-weight: 900;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6, #60a5fa);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientShift 2.5s ease infinite;
}
.icon-stat-label {
    font-size: 15px;
    color: #94a3b8;
    margin-top: 8px;
    font-weight: 500;
}

/* ===== 步骤卡片：滑动移入 ===== */
.step-card {
    display: flex;
    align-items: flex-start;
    gap: 20px;
    margin-bottom: 20px;
    padding: 18px;
    background: rgba(255,255,255,0.02);
    border-radius: 18px;
    transition: background 0.3s, transform 0.3s;
    z-index: 1;
}
.step-card:hover {
    background: rgba(255,255,255,0.08);
    transform: translateX(12px);
}
.step-number {
    background: linear-gradient(135deg, #4361ee, #3a0ca3);
    color: white;
    border-radius: 50%;
    width: 46px; height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 22px;
    flex-shrink: 0;
    box-shadow: 0 6px 18px rgba(67,97,238,0.6);
    animation: stepBounce 1.8s infinite alternate;
}
@keyframes stepBounce {
    0% { transform: scale(1); }
    100% { transform: scale(1.08); }
}

/* ===== 标题：超强流光 + 霓虹发光+呼吸闪烁 ===== */
.main-title {
    font-size: 60px;
    font-weight: 900;
    background: linear-gradient(90deg, #ffffff, #a0c4ff, #60a5fa, #a78bfa, #f472b6);
    background-size: 400% 400%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 4px;
    animation: titleShimmer 4s ease infinite, titleNeonPulse 3s infinite alternate;
    text-shadow: 0 0 40px rgba(96,165,250,0.5);
    position: relative; z-index: 2;
}
@keyframes titleNeonPulse {
    0% { text-shadow:0 0 30px rgba(96,165,250,0.3); }
    100% { text-shadow:0 0 50px rgba(96,165,250,0.7); }
}
.sub-title {
    font-size: 23px;
    color: #93c5fd !important;
    margin-top: 8px;
    margin-bottom: 24px;
    font-weight: 300;
    letter-spacing: 1px;
    position: relative; z-index: 2;
    animation: fadeInUp 1.2s ease-out;
}
.section-title {
    font-size: 30px;
    font-weight: 800;
    color: #e0f2fe !important;
    margin-bottom: 18px;
    border-left: 4px solid #60a5fa;
    padding-left: 20px;
    position: relative; z-index: 2;
}
.caption-text {
    color: #cbd5e1 !important;
    font-size: 17px;
    line-height: 2;
    position: relative; z-index: 2;
    animation: textSweep 8s infinite linear;
}
@keyframes textSweep {
    0% { background-position:-200% 0; }
    100% { background-position:200% 0; }
}

/* ===== 按钮：水波纹 + 呼吸 + 3D按压 + 点击冲击波+内爆 ===== */
.stButton > button {
    background: linear-gradient(90deg, #4361ee, #3a0ca3) !important;
    color: white !important;
    border-radius: 16px !important;
    padding: 14px 32px !important;
    font-weight: 700 !important;
    border: none !important;
    box-shadow: 0 0 25px rgba(67, 97, 238, 0.6) !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    position: relative;
    overflow: hidden;
    z-index: 10;
}
.stButton > button::after {
    content: "";
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 60%);
    animation: buttonPulse 2s infinite;
    pointer-events: none;
}
.stButton > button::before {
    content: "";
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at center, rgba(255,255,255,0.25) 0%, transparent 70%);
    transform: scale(0);
    transition: transform 0.5s ease;
}
.stButton > button:active::before {
    transform: scale(2.5);
    opacity:0;
}
.stButton > button:hover::before {
    transform: scale(2.2);
}
.stButton > button:hover {
    transform: translateY(-8px) scale(1.05);
    box-shadow: 0 0 50px rgba(67, 97, 238, 1), 0 15px 30px rgba(0,0,0,0.3) !important;
}
.stButton > button:active {
    transform: translateY(0) scale(0.98);
}

/* ===== 输入框/下拉框/单选复选：聚焦发光 + 霓虹 + 悬浮 ===== */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {
    background: rgba(15,23,42,0.8) !important;
    border: 1px solid rgba(77,166,255,0.4) !important;
    border-radius: 14px !important;
    color: white !important;
    transition: all 0.3s;
    position: relative; z-index: 10;
}
.stTextInput > div > div > input:focus,
.stSelectbox > div > div > div:focus,
.stNumberInput > div > div > input:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 20px rgba(96,165,250,0.5) !important;
    transform: scale(1.02);
}
.stRadio label, .stCheckbox label {
    background: rgba(255,255,255,0.03);
    padding:12px 20px;
    border-radius:12px;
    border:1px solid rgba(255,255,255,0.08);
    transition:all 0.3s;
}
.stRadio label:hover, .stCheckbox label:hover {
    background:rgba(255,255,255,0.08);
    border-color:rgba(77,166,255,0.4);
    box-shadow:0 0 15px rgba(96,165,250,0.2);
}

/* ===== 所有组件强制上层显示 ===== */
.stMarkdown, .stAlert, .stTabs, [data-testid="stMetric"], 
.stRadio, .stCheckbox, .stExpander, .stPlotlyChart {
    position: relative !important;
    z-index: 10 !important;
}

/* ===== 动画定义 ===== */
@keyframes scanRotate {
    0% { transform: rotate(0deg) translate(-30%, -30%); }
    100% { transform: rotate(360deg) translate(-30%, -30%); }
}
@keyframes borderGlow {
    0% { opacity: 0.4; }
    100% { opacity: 1; }
}
@keyframes glowPulse {
    0% { box-shadow: 0 0 20px rgba(67,97,238,0.25); }
    100% { box-shadow: 0 0 40px rgba(67,97,238,0.5); }
}
@keyframes titleShimmer {
    0%,100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}
@keyframes gradientShift {
    0%,100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}
@keyframes buttonPulse {
    0% { transform: translate(-20%, -20%) scale(0.8); opacity: 0.7; }
    50% { transform: translate(20%, 20%) scale(1.4); opacity: 1; }
    100% { transform: translate(-20%, -20%) scale(0.8); opacity: 0.7; }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ===== 滚动条美化 ===== */
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); border-radius: 10px; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #4361ee, #3a0ca3);
    border-radius: 10px;
    border: 2px solid rgba(0,0,0,0.4);
}
::-webkit-scrollbar-thumb:hover { background: linear-gradient(135deg, #60a5fa, #a78bfa); }
</style>
""", unsafe_allow_html=True)

# =========================
# 页面状态管理
# =========================
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'history' not in st.session_state:
    st.session_state.history = []
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'  # 默认深色；可在顶部一键切换为浅色
if 'lang' not in st.session_state:
    st.session_state.lang = 'zh'  # 默认中文；可在顶部一键切换中/英文

def go_to(page_name):
    st.session_state.page = page_name

def toggle_theme():
    """在深色 / 浅色之间切换。由顶部主题按钮的 on_click 调用。"""
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

def toggle_lang():
    """在中文 / 英文之间切换。由顶部语言按钮的 on_click 调用。"""
    st.session_state.lang = 'en' if st.session_state.lang == 'zh' else 'zh'

# 国际化文案集中在 i18n.py（纯函数、不依赖 streamlit，便于测试）
import i18n as _i18n


def t(key):
    """按当前会话语言取译文。薄包装：实际查表逻辑在可测的 i18n.t 中。"""
    return _i18n.t(key, st.session_state.get('lang', 'zh'))


# 模型与校验函数集中在 pharmacokinetic_models.py（不依赖 streamlit，便于测试）
from pharmacokinetic_models import (
    pk_3comp,
    pk_long_acting,
    tfv_dp_model,
    protection_prob,
    validate_single_score,
    validate_social_attitude,
    validate_behavior_input,
    validate_exposure_input,
    validate_non_negative_numeric,
    behavior_prob_original,
    behavior_prob_multiply,
    behavior_prob,
    pep_priority_score,
    prep_need_prob,
    hiv_transmission_prob,
    sir_simulation,
    score,
    score_protection,
    combined_risk_score,
    numerical_stability_test,
    batch_risk_analysis,
)

# 进阶模型模块（均为纯 numpy / 标准库，不依赖 streamlit，可独立测试，详见 tests/unit/）。
# 这些模块在「高级工具」页面被调用，与既有页面逻辑解耦：导入失败也不影响主功能。
try:
    import pk_advanced as _pk_adv
    import dosing_calculator as _dose
    import adherence as _adh
    import risk_assessment as _risk
    import drug_interactions as _ddi
    import lab_interpretation as _lab
    import epidemiology as _epi
    import viral_dynamics as _vd
    import clinical_guidelines as _guide
    import cost_effectiveness as _cea
    import prevention_knowledge as _know
    import statistics_toolkit as _stats
    _ADVANCED_MODULES_OK = True
except Exception as _adv_import_err:  # pragma: no cover - 仅在缺依赖时触发
    _ADVANCED_MODULES_OK = False
    _ADVANCED_IMPORT_ERR = _adv_import_err

# =========================
# 主题系统：深色（默认）/ 浅色双主题
# =========================
# 设计说明：
#   上方约 348~717 行的静态 <style> 是「深色主题」基线（保持原样，零回归风险）。
#   浅色主题不修改基线，而是在其之后再注入一段更高优先级（!important）的覆盖样式，
#   利用 CSS 层叠「后者胜出 + !important 覆盖内联样式」的规则把深色配色翻成浅色。
#
#   难点：页面正文里散落着大量内联 `style="color:#xxx"`（约 70 处），普通选择器无法
#   覆盖内联样式。这里用「属性子串选择器」`[style*="color:#xxx"]` 精确命中每一种深色
#   文字色，并 !important 映射到一个在白底上可读、且尽量保留语义（绿=安全/红=警示/
#   黄=提示/蓝=信息）的深色等价色。如此无需改动任何正文 HTML 即可保证可读性。

# 深色文字色 → 浅色主题下的可读等价色。
# 原则：浅色模式 = 白底黑字，严禁低对比灰色。普通文字一律压到近黑（#111827），
# 仅保留承载语义的强调色（蓝=信息、绿=安全、黄=注意、红=警示），且都取“深而饱和”的
# 版本，确保在纯白底上清晰可辨。
LIGHT_TEXT_REMAP = {
    "#cbd5e1": "#111827",  # 正文次要灰 → 近黑（杜绝灰字）
    "#93c5fd": "#1e3a8a",  # 浅蓝小标题 → 深蓝
    "#94a3b8": "#111827",  # 辅助说明灰 → 近黑（杜绝灰字）
    "#e0f2fe": "#0b1f33",  # 区块大标题浅蓝 → 极深青蓝
    "#60a5fa": "#1d4ed8",  # 强调蓝 → 深蓝
    "#4ade80": "#15803d",  # 安全绿 → 深绿（保留“安全/正向”语义）
    "#facc15": "#a16207",  # 提示黄 → 深琥珀（保留“注意”语义）
    "#f87171": "#b91c1c",  # 警示红 → 深红（保留“危险/紧急”语义）
}


def _build_light_theme_css():
    """构造浅色主题覆盖样式字符串。集中在此函数，便于维护与单独测试调色。"""
    # 由配色表自动生成内联色覆盖规则，新增/调整配色只改 LIGHT_TEXT_REMAP 即可
    inline_rules = "\n".join(
        f'[style*="color:{dark}"] {{ color:{light} !important; }}'
        for dark, light in LIGHT_TEXT_REMAP.items()
    )
    return f"""
<style>
/* ===================== 浅色主题覆盖层（仅在浅色模式注入） ===================== */
/* 目标：纯白底 + 纯黑字，与深色模式形成强对比。严禁低对比灰字。 */

/* 1) 可见背景层 = .stApp / 视图容器 / 顶栏，全部强制纯白
      （只改 body 没用：Streamlit 的 .stApp 盖在 body 之上才是真正可见的底） */
html, body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .block-container,
[data-testid="stHeader"] {{
    background: #ffffff !important;
    color: #000000 !important;
}}

/* 2) 兜底：应用内所有常规文字元素一律纯黑（强调色由第 9 节精确映射覆盖） */
.stApp, .stApp p, .stApp li, .stApp span, .stApp label,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stMarkdown, [data-testid="stMarkdownContainer"] {{
    color: #000000 !important;
}}

/* 3) 背景粒子动画在白底上几乎不可见，整体压暗避免杂乱 */
#main-canvas {{ opacity: 0.22 !important; }}

/* 4) 主卡片：纯白底 + 清晰边框 + 黑字（去掉深色渐变与内发光） */
.main-card {{
    background: #ffffff !important;
    border: 1px solid #1d4ed8 !important;
    box-shadow: 0 6px 24px rgba(15,23,42,0.12) !important;
    color: #000000 !important;
}}
.main-card::before {{ background: none !important; }}
.main-card::after {{ background: linear-gradient(60deg, #1d4ed8, #7c3aed, #db2777) !important; }}

/* 5) 次级 / 高亮 / 统计 / 步骤卡片：浅底深框黑字 */
.card {{
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    color: #000000 !important;
}}
.card:hover {{
    box-shadow: 0 16px 32px rgba(37,99,235,0.18) !important;
    border-color: #1d4ed8 !important;
}}
.highlight-card {{
    background: #eff6ff !important;
    border: 1px solid #1d4ed8 !important;
    color: #000000 !important;
}}
.icon-stat-card {{
    background: #f1f5f9 !important;
    border: 1px solid #cbd5e1 !important;
}}
.icon-stat-label {{ color: #000000 !important; }}
.step-card {{ background: #f1f5f9 !important; }}
.step-card:hover {{ background: #e2e8f0 !important; }}

/* 6) 渐变文字（主标题、统计数字）：白底上必须用「深色渐变」，否则透明字色 + 浅色
      渐变会几乎不可见。这里统一改成深蓝→深紫→深玫红，每个色段在白底上对比度都足够。 */
.main-title, .icon-stat-number {{
    background: linear-gradient(90deg, #1e3a8a, #6b21a8, #9d174d) !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    text-shadow: none !important;
}}
.sub-title {{ color: #1e3a8a !important; }}
.section-title {{ color: #0b1f33 !important; border-left-color: #1d4ed8 !important; }}
.caption-text {{ color: #000000 !important; }}

/* 7) 按钮：浅底黑字 + 蓝框（含首页大按钮与普通操作按钮）。
      顶部语言/主题小按钮在第 10 节单独定义，不受此影响。 */
div[data-testid="stButton"] button:not(.st-key-lang_toggle button):not(.st-key-theme_toggle button),
.stButton > button {{
    background: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #1d4ed8 !important;
    box-shadow: 0 2px 10px rgba(29,78,216,0.18) !important;
}}
div[data-testid="stButton"] button:hover {{
    background: #eff6ff !important;
    border-color: #1e3a8a !important;
}}

/* 8) 输入控件：白底黑字 */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {{
    background: #ffffff !important;
    border: 1px solid #1d4ed8 !important;
    color: #000000 !important;
}}
.stRadio label, .stCheckbox label {{
    background: #f1f5f9 !important;
    border: 1px solid #cbd5e1 !important;
    color: #000000 !important;
}}
.stRadio label:hover, .stCheckbox label:hover {{ background: #dbeafe !important; }}

/* 8b) Streamlit 内置组件文字：因基底为深色，这些组件默认白字，必须在浅色模式强制黑字，
       否则点击计算后出现的 st.metric 指标、tab 标签、expander、caption 等会“白字白底”看不见。
       st.metric 的数值是 <div> 而非 p/span，前面的通用规则覆盖不到，这里显式补齐。 */
[data-testid="stMetricValue"], [data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *, [data-testid="stMetricValue"] *,
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] *,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary *,
[data-baseweb="tab"], [data-baseweb="tab"] *,
button[role="tab"], button[role="tab"] *,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{
    color: #000000 !important;
    fill: #000000 !important;
    opacity: 1 !important;  /* caption 默认 opacity:0.6 会让黑字显灰，强制不透明 */
}}

/* 8c) baseweb 输入控件（日期/下拉/数字/文本框/下拉菜单）：基底深色会让它们呈深底，
       这里统一翻成白底黑字，与浅色主题一致。 */
[data-baseweb="input"], [data-baseweb="base-input"],
[data-baseweb="input"] input, [data-baseweb="base-input"] input,
[data-baseweb="select"] > div, [data-baseweb="select"] div[role="button"],
.stDateInput input, .stTextArea textarea, .stTimeInput input,
[data-baseweb="textarea"], [data-baseweb="textarea"] textarea {{
    background: #ffffff !important;
    color: #000000 !important;
    border-color: #1d4ed8 !important;
}}
/* 下拉菜单弹层（打开 selectbox 时出现的列表）也翻白底黑字 */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] ul,
[data-baseweb="menu"], [data-baseweb="menu"] li {{
    background: #ffffff !important;
    color: #000000 !important;
}}
[data-baseweb="menu"] li:hover {{ background: #dbeafe !important; }}

/* 9) 滚动条：浅色轨道 */
::-webkit-scrollbar-track {{ background: #e2e8f0 !important; }}
::-webkit-scrollbar-thumb {{ border: 2px solid #ffffff !important; }}

/* 10) 侧边栏：纯白底黑字 */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{ background: #ffffff !important; }}
[data-testid="stSidebar"] * {{ color: #000000 !important; }}
[data-testid="stSidebar"] [data-testid="stAlert"] {{ background: #eff6ff !important; }}

/* 11) 内联颜色精确映射（覆盖正文里散落的 style="color:#xxx"，把深色字翻成白底可读色） */
{inline_rules}
</style>
"""


def render_global_controls():
    """在「侧边栏顶部」（关于本平台 上方）渲染语言 / 主题两个普通小按钮。

    它们是全局设置，放侧边栏最合适。用 .st-key-* 类（Streamlit 1.39+ 为带 key 组件
    自动附加）把按钮压成普通小尺寸，避免被首页 150px 大按钮规则放大。
    因为这些 st.sidebar.* 调用在脚本中最早执行，会自然排在侧边栏最顶部。
    """
    st.markdown(
        """
<style>
/* 侧边栏作用域 + 双属性选择器，特异性(0,2,1)高于首页 150px 大按钮规则(0,1,2)，
   保证这两个全局开关在任何页面都是普通小按钮 */
[data-testid="stSidebar"] [data-testid="stButton"] button {
    height: 36px !important;
    min-height: 36px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 4px 10px !important;
    border-radius: 8px !important;
    white-space: nowrap !important;
}
</style>
""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.sidebar.columns(2)
    with c1:
        # 语言切换：按钮显示「下一个语言」
        st.button(
            _i18n.LANG_SWITCH_LABEL.get(st.session_state.lang, "🌐 EN"),
            key="lang_toggle", on_click=toggle_lang, use_container_width=True,
        )
    with c2:
        # 主题切换：中英文都给出对应文案
        if st.session_state.lang == 'en':
            theme_label = "🌞 Light" if st.session_state.theme == 'dark' else "🌙 Dark"
        else:
            theme_label = "🌞 浅色" if st.session_state.theme == 'dark' else "🌙 深色"
        st.button(theme_label, key="theme_toggle", on_click=toggle_theme, use_container_width=True)


# 浅色模式下注入覆盖样式（深色模式走 .streamlit/config.toml 的深色基底，基线零改动）
if st.session_state.theme == 'light':
    st.markdown(_build_light_theme_css(), unsafe_allow_html=True)

# 全局语言 / 主题切换按钮（渲染在侧边栏顶部，所有页面通用）
render_global_controls()


PLATFORM_NAME = "知药护身·护佑零艾 数字化PrEP健康管理平台"
REPORT_DISCLAIMER = (
    "本报告由知药护身® PrEP伴行健康管理平台根据用户输入自动生成，仅用于健康教育、"
    "风险沟通和自我管理参考，不能替代医生面诊、HIV检测、实验室检查或处方建议。"
    "如近期发生可能暴露，尤其在72小时内，请优先前往医疗机构评估PEP。"
)


def render_platform_hero():
    st.markdown("""
    <div class="main-card">
        <p class="main-title">知药护身·护佑零艾</p>
        <p class="sub-title">风险评估、检测筛查、智能干预、医疗转诊一体化数字防艾服务平台。</p>
        <p class="caption-text">
        面向普通用户的PrEP启动决策、服药打卡、漏服补救、保护曲线与个人评估报告工具。
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_journey_entry(label, title, body, bullets):
    items = "".join([f"<li>{item}</li>" for item in bullets])
    st.markdown(f"""
    <div class="card" style="min-height:220px;">
        <p style="color:#38bdf8;font-weight:800;margin-bottom:8px;">{label}</p>
        <h2 style="color:#e0f2fe;margin-top:0;">{title}</h2>
        <p class="caption-text" style="text-align:left;">{body}</p>
        <ul style="color:#dbeafe;line-height:1.8;">{items}</ul>
    </div>
    """, unsafe_allow_html=True)


def pep_priority_text(score, exposure):
    if exposure == "有，72小时以内" or score >= 70:
        return "PEP优先级高：请把PEP当作今天的第一优先级，尽快到医院/疾控/VCT门诊评估。"
    if exposure == "有，超过72小时":
        return "已超过PEP最佳窗口：仍建议尽快检测并咨询医生，安排后续HIV检测时间。"
    if score >= 40:
        return "PEP优先级中等：如暴露细节不确定，建议咨询专业人员确认是否需要PEP。"
    return "目前没有明确PEP紧急信号：继续关注检测窗口期和日常预防。"


def prep_advice_text(need):
    if need > 0.7:
        return "建议尽快启动PrEP评估：在确认HIV阴性、肾功能等检查合适后，由医生指导用药。"
    if need > 0.4:
        return "建议主动咨询PrEP：如果类似行为会重复发生，PrEP可能比事后焦虑更可控。"
    return "暂不属于强启动PrEP场景：继续使用安全套、定期检测；如果风险模式改变，可重新评估。"


def behavior_level_text(prob):
    if prob >= 0.6:
        return "高行为风险"
    if prob >= 0.25:
        return "中行为风险"
    return "低行为风险"


def protection_level_text(score_value, risk):
    if score_value > 70:
        return "当前保护较稳"
    if score_value > 40:
        return "当前仍有部分保护"
    if risk == "高风险":
        return "当前保护可能不足"
    return "当前保护需要复核"


def calculate_protection(drug_regimen, days, miss, behavior_prob_value):
    if drug_regimen == "TDF/FTC (每日口服)":
        conc, current, remain, threshold = pk_3comp(days, miss, 300, 0.5, 0.3, 0.2, 0.15, 700)
        prot_prob = protection_prob(current, 700, 100)
        improved_days = min(days + 7, 30)
        improved_miss = max(miss - 1, 0)
        conc2, current2, remain2, _ = pk_3comp(improved_days, improved_miss, 300, 0.5, 0.3, 0.2, 0.15, 700)
        prot_prob2 = protection_prob(current2, 700, 100)
        improve_note = f"建议接下来{improved_days}天尽量规律服药，并把漏服控制在{improved_miss}天以内。"
    elif drug_regimen == "TAF/FTC (每日口服)":
        conc, current, remain, threshold = pk_3comp(days, miss, 200, 0.6, 0.35, 0.25, 0.18, 600)
        prot_prob = protection_prob(current, 600, 100)
        improved_days = min(days + 7, 30)
        improved_miss = max(miss - 1, 0)
        conc2, current2, remain2, _ = pk_3comp(improved_days, improved_miss, 200, 0.6, 0.35, 0.25, 0.18, 600)
        prot_prob2 = protection_prob(current2, 600, 100)
        improve_note = f"建议接下来{improved_days}天尽量规律服药，并把漏服控制在{improved_miss}天以内。"
    else:
        conc, current, remain, threshold = pk_long_acting(days, 600, 0.2, 0.05, 200)
        prot_prob = protection_prob(current, 200, 100)
        improved_days = min(days + 7, 30)
        conc2, current2, remain2, _ = pk_long_acting(improved_days, 600, 0.2, 0.05, 200)
        prot_prob2 = protection_prob(current2, 200, 100)
        improve_note = f"建议按预约完成下一次注射；若距离上次注射已{days}天，请按医嘱复核保护状态。"

    status, risk, score_value = score_protection(behavior_prob_value, remain)
    status2, risk2, score2 = score_protection(min(behavior_prob_value + 0.1, 1), remain2)
    return {
        "conc": conc,
        "current": float(current),
        "remain": float(remain),
        "threshold": float(threshold),
        "prot_prob": float(prot_prob),
        "conc2": conc2,
        "remain2": float(remain2),
        "prot_prob2": float(prot_prob2),
        "status": status,
        "risk": risk,
        "score": int(score_value),
        "status2": status2,
        "risk2": risk2,
        "score2": int(score2),
        "improve_note": improve_note,
    }


def build_prep_report(user_id, pep_text, prep_text, protection_text, protection_score, remain, advice):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""# 个人PrEP保护状态评估报告

平台：{PLATFORM_NAME}

| 项目 | 结果 |
| --- | --- |
| 用户编号 | {user_id or "未填写"} |
| 评估时间 | {now} |
| PEP优先级 | {pep_text} |
| PrEP启动建议 | {prep_text} |
| 当前保护状态 | {protection_text} |
| 保护指数 | {protection_score}/100 |
| 剩余保护窗口 | {remain:.1f} 天 |
| 个性化建议 | {advice} |

## 免责声明

{REPORT_DISCLAIMER}
"""


def render_report_download(report_text, key):
    st.download_button(
        "生成个人PrEP保护状态评估报告",
        data=report_text,
        file_name=f"prep_protection_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
        key=key,
        use_container_width=True,
    )


# =========================
# 首页
# =========================
if st.session_state.page == 'home':
    render_platform_hero()

    # 首页数据概览
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="icon-stat-card"><div class="icon-stat-number">{t('home.stat.pep_window.num')}</div><div class="icon-stat-label">{t('home.stat.pep_window.label')}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="icon-stat-card"><div class="icon-stat-number">{t('home.stat.prep_rate.num')}</div><div class="icon-stat-label">{t('home.stat.prep_rate.label')}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="icon-stat-card"><div class="icon-stat-number">{t('home.stat.fourinone.num')}</div><div class="icon-stat-label">{t('home.stat.fourinone.label')}</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="icon-stat-card"><div class="icon-stat-number">{t('home.stat.threestep.num')}</div><div class="icon-stat-label">{t('home.stat.threestep.label')}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#e0f2fe; margin:30px 0 20px;'>先选择你现在处在哪一步</h2>", unsafe_allow_html=True)

    start_col, manage_col = st.columns(2)
    with start_col:
        render_journey_entry(
            "入口一",
            "我尚未使用PrEP",
            "用于回答：我需不需要PEP？我需不需要PrEP？下一步该找谁？",
            ["PEP紧急优先级判断", "PrEP启动建议", "行为风险等级", "建议行动与医疗转介提示"],
        )
        if st.button("进入 PrEP启动决策中心", key="entry_start_center", use_container_width=True):
            go_to("PrEP启动决策中心")
    with manage_col:
        render_journey_entry(
            "入口二",
            "我正在使用PrEP",
            "用于回答：我现在还有没有保护？漏服后怎么办？停药后还能保护多久？",
            ["每日服药打卡", "漏服记录", "保护状态日志", "保护曲线", "剩余保护窗口与当前保护等级"],
        )
        if st.button("进入 PrEP保护状态管理中心", key="entry_manage_center", use_container_width=True):
            go_to("PrEP保护状态管理中心")

    st.markdown("<h2 style='text-align:center; color:#e0f2fe; margin:34px 0 18px;'>评估—检测—干预—转诊核心闭环</h2>", unsafe_allow_html=True)
    core_col1, core_col2 = st.columns(2)
    with core_col1:
        if st.button("风险评估中心\n暴露 / 行为 / PrEP / PEP / KAP", key="card_core_risk", use_container_width=True):
            go_to('风险评估中心')
    with core_col2:
        if st.button("检测筛查中心\n尿液 / 血液 / 核酸检测推荐", key="card_core_screening", use_container_width=True):
            go_to('检测筛查中心')
    core_col3, core_col4 = st.columns(2)
    with core_col3:
        if st.button("安全预哨所智能终端\n试纸识别 / C线T线 / 结果上传", key="card_core_terminal", use_container_width=True):
            go_to('安全预哨所智能终端')
    with core_col4:
        if st.button("智能干预中心\n检测 / PrEP / PEP / 药学指导", key="card_core_intervention", use_container_width=True):
            go_to('智能干预中心')
    core_col5, core_col6 = st.columns(2)
    with core_col5:
        if st.button("医疗服务中心\n检测机构 / 社区医院 / PrEP与PEP门诊", key="card_core_medical", use_container_width=True):
            go_to('医疗服务中心')
    with core_col6:
        if st.button("系统架构与接口设计\n架构图 / ER图 / API / 数据库", key="card_core_design", use_container_width=True):
            go_to('系统架构与接口设计')
    core_col7, core_col8 = st.columns(2)
    with core_col7:
        if st.button("终端上传报告\nESP32上传数据 / 报告列表 / JSON查看", key="card_core_terminal_reports", use_container_width=True):
            go_to('终端上传报告')
    with core_col8:
        st.empty()
    st.markdown("<h2 style='text-align:center; color:#e0f2fe; margin:34px 0 18px;'>更多科普与模型工具</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t('nav.kepu'), key="card_1", use_container_width=True):
            go_to('科普')
    with col2:
        if st.button(t('nav.risk'), key="card_2", use_container_width=True):
            go_to('风险')
    col3, col4 = st.columns(2)
    with col3:
        if st.button(t('nav.medical'), key="card_3", use_container_width=True):
            go_to('医疗')
    with col4:
        if st.button(t('nav.assess'), key="card_4", use_container_width=True):
            go_to('评估')
    col5, col6 = st.columns(2)
    with col5:
        if st.button(t('nav.insight'), key="card_5", use_container_width=True):
            go_to('数据洞察')
    with col6:
        if st.button(t('nav.tools'), key="card_6", use_container_width=True):
            go_to('个人工具')
    col7, col8 = st.columns(2)
    with col7:
        if st.button(t('nav.policy'), key="card_7", use_container_width=True):
            go_to('政策')
    with col8:
        if st.button(t('nav.story'), key="card_8", use_container_width=True):
            go_to('故事')
    col9, col10 = st.columns(2)
    with col9:
        if st.button("🧪 进阶模型工具\n药代 / 风险 / 依从性 / 用药安全", key="card_9", use_container_width=True):
            go_to('高级工具')
    with col10:
        if st.button("📚 知识库与流行病学\n术语检索 / 传播模拟 / 卫生经济", key="card_10", use_container_width=True):
            go_to('知识库')

    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        height: 150px !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        border-radius: 24px !important;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(30, 58, 138, 0.5)) !important;
        border: 1px solid rgba(77, 166, 255, 0.3) !important;
        white-space: pre-line !important;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-8px);
        border-color: rgba(56, 189, 248, 0.6) !important;
        box-shadow: 0 0 35px rgba(56, 189, 248, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# 公共科普页（大幅丰富）
# =========================
elif render_new_service_loop_pages(st.session_state.page):
    pass
elif st.session_state.page == '科普':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown(t("kepu.section_card"), unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        t("kepu.tab.knowledge"), t("kepu.tab.campus"), t("kepu.tab.community"),
        t("kepu.tab.myths"), t("kepu.tab.progress"),
    ])

    with tab1:
        st.markdown(t("kepu.t1.heading"))
        st.markdown(t("kepu.t1.what_is_hiv"), unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(t("kepu.t1.transmission"), unsafe_allow_html=True)
        with col_b:
            st.markdown(t("kepu.t1.prevention"), unsafe_allow_html=True)

        st.markdown(t("kepu.t1.prep_pep_heading"))
        prep_col, pep_col = st.columns(2)
        with prep_col:
            st.markdown(t("kepu.t1.prep"), unsafe_allow_html=True)
        with pep_col:
            st.markdown(t("kepu.t1.pep"), unsafe_allow_html=True)

    with tab2:
        st.markdown(t("kepu.t2.heading"))
        st.markdown(t("kepu.t2.subtitle"), unsafe_allow_html=True)
        show_image("img/campus.png")
        show_image("img/campus2.png")
        st.markdown(t("kepu.t2.tips"), unsafe_allow_html=True)

    with tab3:
        st.markdown(t("kepu.t3.heading"))
        st.markdown(t("kepu.t3.subtitle"), unsafe_allow_html=True)
        show_image("img/community.png")
        st.markdown(t("kepu.t3.tips"), unsafe_allow_html=True)

    with tab4:
        st.markdown(t("kepu.t4.heading"))
        for q, a in t("kepu.t4.myths"):
            st.markdown(f"""<div class="card"><p class="faq-q">{q}</p><p class="faq-a">{a}</p></div>""", unsafe_allow_html=True)

    with tab5:
        st.markdown(t("kepu.t5.heading"))
        st.markdown(t("kepu.t5.art"), unsafe_allow_html=True)

# =========================
# 风险认知页（大幅丰富）
# =========================
elif st.session_state.page == '风险':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown(t("risk.section_card"), unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([t("risk.tab.self"), t("risk.tab.levels"), t("risk.tab.support")])

    with tab1:
        st.markdown(t("risk.t1.heading"))
        scenarios = t("risk.t1.scenarios")
        labels = [s["label"] for s in scenarios]
        scenario = st.selectbox(t("risk.t1.select_label"), labels)

        if st.button(t("risk.t1.get_assessment")):
            s = next(x for x in scenarios if x["label"] == scenario)
            # 用结构化字段驱动展示，避免按中文子串匹配（双语通用）
            {"success": st.success, "warning": st.warning, "error": st.error}[s["level"]](s["title"])
            st.write(s["body"])
            {"info": st.info, "error": st.error}[s["tip_level"]](s["tip"])

    with tab2:
        st.markdown(t("risk.t2.heading"))
        st.markdown(t("risk.t2.subtitle"), unsafe_allow_html=True)
        for level, behavior_type, detail, action in t("risk.t2.data"):
            st.markdown(f"""
            <div class="card">
            <h4 style="margin:0 0 8px 0;">{level} · {behavior_type}</h4>
            <p style="color:#cbd5e1; margin:0 0 4px 0;">{detail}</p>
            <p style="color:#94a3b8; font-size:14px; margin:0;">→ {action}</p>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown(t("risk.t3.heading"))
        st.markdown(t("risk.t3.anxiety_card"), unsafe_allow_html=True)

        st.markdown(t("risk.t3.support_heading"))
        support_col1, support_col2 = st.columns(2)
        with support_col1:
            st.markdown(t("risk.t3.hotline_card"), unsafe_allow_html=True)
        with support_col2:
            st.markdown(t("risk.t3.vct_card"), unsafe_allow_html=True)

        st.markdown(t("risk.t3.fear_card"), unsafe_allow_html=True)

# =========================
# 医疗支持页（大幅丰富）
# =========================
elif st.session_state.page == '医疗':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown(t("medical.section_card"), unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        t("medical.tab.test"), t("medical.tab.path"), t("medical.tab.get"), t("medical.tab.online"),
    ])

    with tab1:
        st.markdown(t("medical.t1.heading"))
        st.markdown(t("medical.t1.window_card"), unsafe_allow_html=True)

        test_col1, test_col2, test_col3 = st.columns(3)
        with test_col1:
            st.markdown(t("medical.t1.test4"), unsafe_allow_html=True)
        with test_col2:
            st.markdown(t("medical.t1.test3"), unsafe_allow_html=True)
        with test_col3:
            st.markdown(t("medical.t1.nat"), unsafe_allow_html=True)

        st.markdown(t("medical.t1.where_heading"))
        st.markdown(t("medical.t1.where_table"), unsafe_allow_html=True)

    with tab2:
        st.markdown(t("medical.t2.heading"))
        st.markdown(t("medical.t2.subtitle"), unsafe_allow_html=True)
        st.markdown(t("medical.t2.pep_path"), unsafe_allow_html=True)
        st.markdown(t("medical.t2.prep_path"), unsafe_allow_html=True)
        st.markdown(t("medical.t2.test_path"), unsafe_allow_html=True)

    with tab3:
        st.markdown(t("medical.t3.heading"))

        st.markdown(t("medical.t3.pep_steps_heading"), unsafe_allow_html=True)
        pep_color = t("medical.t3.pep_color")
        for i, (title, desc) in enumerate(t("medical.t3.pep_steps"), 1):
            st.markdown(f"""
            <div class="step-card"><div class="step-number">{i}</div><div class="step-content"><strong style="color:{pep_color};">{title}</strong><br><span style="color:#cbd5e1;">{desc}</span></div></div>
            """, unsafe_allow_html=True)

        st.markdown(t("medical.t3.prep_steps_heading"), unsafe_allow_html=True)
        prep_color = t("medical.t3.prep_color")
        for i, (title, desc) in enumerate(t("medical.t3.prep_steps"), 1):
            st.markdown(f"""
            <div class="step-card"><div class="step-number">{i}</div><div class="step-content"><strong style="color:{prep_color};">{title}</strong><br><span style="color:#cbd5e1;">{desc}</span></div></div>
            """, unsafe_allow_html=True)

    with tab4:
        st.markdown(t("medical.t4.heading"))

        resource_col1, resource_col2 = st.columns(2)
        with resource_col1:
            st.markdown(t("medical.t4.hotline_card"), unsafe_allow_html=True)
        with resource_col2:
            st.markdown(t("medical.t4.cdc_card"), unsafe_allow_html=True)

        st.markdown(t("medical.t4.channels_card"), unsafe_allow_html=True)

# =========================
# PrEP伴行双中心
# =========================
elif st.session_state.page in ('评估', 'PrEP启动决策中心', 'PrEP保护状态管理中心'):
    if st.button(t("common.back_home")):
        go_to('home')

    default_user_type = "已经在使用PrEP" if st.session_state.page == "PrEP保护状态管理中心" else "尚未使用PrEP"
    if st.session_state.page == "评估":
        center_mode = st.radio(
            "请选择当前状态",
            ["我尚未使用PrEP", "我正在使用PrEP"],
            horizontal=True,
        )
        default_user_type = "尚未使用PrEP" if center_mode == "我尚未使用PrEP" else "已经在使用PrEP"

    if default_user_type == "尚未使用PrEP":
        st.markdown("""
        <div class="main-card">
            <p class="main-title">PrEP启动决策中心</p>
            <p class="sub-title">先排除PEP紧急情况，再判断是否适合进入PrEP启动评估。</p>
            <p class="caption-text">回答几个问题，系统会给出PEP优先级、PrEP启动建议、行为风险等级、建议行动和医疗转介提示。</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="main-card">
            <p class="main-title">PrEP保护状态管理中心</p>
            <p class="sub-title">用打卡和保护曲线看见：今天是否仍有保护、漏服后怎么办、停药后还能保护多久。</p>
            <p class="caption-text">记录每日服药、漏服天数和当前方案，系统会估算保护指数、剩余保护窗口和当前保护等级。</p>
        </div>
        """, unsafe_allow_html=True)

    st.info("本工具仅用于健康教育与自我管理参考。发生可能暴露后72小时内，请优先线下评估PEP。")

    user_id = st.text_input("用户编号（用于报告，可匿名填写）", value="PREP-" + datetime.now().strftime("%Y%m%d"))
    c_exp, c_beh = st.columns(2)
    with c_exp:
        exposure = st.radio("最近是否有可能暴露？", ["没有明确近期暴露", "有，72小时以内", "有，超过72小时"])
    with c_beh:
        behavior = st.radio("最近行为风险频率", ["无高风险行为", "偶尔风险行为", "频繁高风险行为"])

    c_soc, c_moral = st.columns(2)
    with c_soc:
        social = st.selectbox("你对日常社交风险的判断", ["正常交往", "不确定", "保持距离", "不接触"])
        s = {"正常交往": 1, "不确定": 2, "保持距离": 3, "不接触": 4}[social]
    with c_moral:
        moral = st.selectbox("你如何理解HIV预防", ["公共卫生问题", "部分个人行为", "道德问题"])
        m = {"公共卫生问题": 1, "部分个人行为": 3, "道德问题": 5}[moral]

    p = behavior_prob(s, m, behavior)
    pep_score = pep_priority_score(exposure, behavior)
    pep_text = pep_priority_text(pep_score, exposure)
    prep_need = prep_need_prob(s, m, behavior, exposure)
    prep_text = prep_advice_text(prep_need)
    behavior_level = behavior_level_text(p)

    if default_user_type == "尚未使用PrEP":
        st.markdown("### 你的启动决策结果")
        r1, r2, r3 = st.columns(3)
        r1.metric("PEP优先级", f"{pep_score}/100")
        r2.metric("PrEP启动建议指数", f"{prep_need * 100:.1f}%")
        r3.metric("行为风险等级", behavior_level)

        if pep_score >= 70:
            st.error(pep_text)
        elif pep_score >= 40:
            st.warning(pep_text)
        else:
            st.success(pep_text)

        if prep_need > 0.7:
            st.error(prep_text)
        elif prep_need > 0.4:
            st.warning(prep_text)
        else:
            st.success(prep_text)

        st.markdown("### 建议行动")
        st.write("1. 我需不需要PEP？如果在72小时内发生可能暴露，请先线下评估PEP，越早越好。")
        st.write("2. 我需不需要PrEP？如果风险会重复出现，建议做HIV、肾功能、乙肝等检查后咨询PrEP。")
        st.write("3. 医疗转介提示：可选择感染科、皮肤性病科、疾控/VCT门诊或具备PrEP服务的互联网医院。")

        report = build_prep_report(
            user_id,
            pep_text,
            prep_text,
            "尚未开始PrEP，暂无当前药物保护状态",
            int(prep_need * 100),
            0.0,
            "先处理PEP时间窗，再预约PrEP启动前检查；在启动前继续使用安全套并安排HIV检测。",
        )
        render_report_download(report, "start_report_download")
        st.session_state.history.append(f"启动中心 | 暴露:{exposure} | 行为:{behavior} | PEP:{pep_score} | PrEP:{prep_need:.2f}")

    else:
        st.markdown("### 每日服药打卡与漏服记录")
        drug_regimen = st.selectbox("当前PrEP方案", ["TDF/FTC (每日口服)", "TAF/FTC (每日口服)", "长效注射 (CAB-LA)"])
        today_taken = st.checkbox("今日已按计划服药/完成注射", value=True)
        if today_taken:
            st.success("今日已打卡。继续保持规律用药，保护状态更稳定。")
        else:
            st.warning("今日未打卡。如果是口服PrEP，请尽快查看医嘱或咨询医生确认补服方式。")

        d1, d2 = st.columns(2)
        days = d1.number_input("已连续/本轮使用天数", 0, 30, 7)
        miss = d2.number_input("本轮漏服天数", 0, 10, 2)
        missed_dates = st.multiselect(
            "漏服记录（可选）",
            [f"第{i}天" for i in range(1, int(days) + int(miss) + 1)],
        )

        result = calculate_protection(drug_regimen, int(days), int(miss), p)
        protection_text = protection_level_text(result["score"], result["risk"])
        color = "#22C55E" if result["risk"] == "低风险" else "#FACC15" if result["risk"] == "中风险" else "#EF4444"

        st.markdown(f"""
        <div class="card">
            <h2>当前保护等级</h2>
            <p class="metric-big" style="color:{color}">{protection_text}</p>
            <h3>保护指数：{result["score"]}/100</h3>
            <h3>剩余保护窗口：{result["remain"]:.1f} 天</h3>
        </div>
        """, unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("行为风险", f"{p * 100:.1f}%")
        m2.metric("当前浓度", f"{result['current']:.1f} ng/mL")
        m3.metric("保护概率", f"{result['prot_prob'] * 100:.1f}%")
        m4.metric("漏服记录", f"{len(missed_dates)}条")

        st.markdown("### 漏服后怎么办 / 停药后还能保护多久")
        if result["remain"] <= 0:
            st.error("模型估算当前已低于保护阈值。近期如有暴露，请尽快咨询医生是否需要PEP或重新启动方案。")
        elif result["remain"] < 2:
            st.warning("剩余保护窗口较短。请尽快恢复规律用药，并避免无保护暴露。")
        else:
            st.success(f"按当前模型估算，仍有约{result['remain']:.1f}天保护窗口；规律用药可让保护更稳定。")
        st.info(result["improve_note"])

        st.markdown("### 保护状态日志")
        st.write(f"方案：{drug_regimen}；本轮使用：{days}天；漏服：{miss}天；今日打卡：{'已完成' if today_taken else '未完成'}。")

        st.markdown("### 保护曲线")
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=result["conc"], mode='lines', name="当前记录", line=dict(color='lime', width=4)))
        fig.add_trace(go.Scatter(y=result["conc2"], mode='lines', name="改善后模拟", line=dict(color='cyan', width=3, dash='dash')))
        fig.add_hline(y=result["threshold"], line_dash="dot", line_color="red", annotation_text="保护阈值")
        fig.update_layout(
            xaxis_title="天数",
            yaxis_title="估算浓度",
            plot_bgcolor="#111827",
            paper_bgcolor="#0B1020",
            font=dict(color="white"),
        )
        st.plotly_chart(fig, use_container_width=True)

        report = build_prep_report(
            user_id,
            pep_text,
            prep_text,
            protection_text,
            result["score"],
            result["remain"],
            f"{result['improve_note']} 漏服记录：{', '.join(missed_dates) if missed_dates else '暂无填写'}。",
        )
        render_report_download(report, "manage_report_download")
        st.session_state.history.append(f"保护中心 | 用药:{drug_regimen} | 天数:{days} | 漏服:{miss} | 评分:{result['score']} | 风险:{result['risk']}")

    with st.expander("查看历史评估记录"):
        if st.session_state.history:
            for idx, rec in enumerate(st.session_state.history[-10:]):
                st.write(f"{idx + 1}. {rec}")
        else:
            st.write("暂无记录。")

# =========================
# 数据洞察页（新增）
# =========================
elif st.session_state.page == '数据洞察':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown(t("data.section_card"), unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([t("data.tab1"), t("data.tab2"), t("data.tab3")])

    with tab1:
        st.markdown(t("data.t1_heading"))
        st.markdown(f'<p class="section-subtitle">{t("data.t1_subtitle")}</p>', unsafe_allow_html=True)

        _et_opts = t("data.t1_exposure_opts")
        viral_load = st.slider(t("data.t1_viral"), min_value=50, max_value=1000000, value=50000, step=1000)
        exposure_type = st.selectbox(t("data.t1_exposure"), ["receptive_anal", "insertive_anal", "vaginal", "oral"], format_func=lambda x: _et_opts.get(x, x))
        condom_use = st.checkbox(t("data.t1_condom"), value=True)
        circumcision = st.checkbox(t("data.t1_circ"))
        sti_present = st.checkbox(t("data.t1_sti"))

        prob = hiv_transmission_prob(viral_load, exposure_type, condom_use, circumcision, sti_present)
        st.metric(t("data.t1_metric"), f"{prob*100:.4f}%")
        st.caption(t("data.t1_caption"))

    with tab2:
        st.markdown(t("data.t2_heading"))
        st.markdown(f'<p class="section-subtitle">{t("data.t2_subtitle")}</p>', unsafe_allow_html=True)
        col_beta, col_gamma = st.columns(2)
        with col_beta:
            beta = st.slider(t("data.t2_beta"), 0.01, 0.5, 0.15, 0.01)
        with col_gamma:
            gamma = st.slider(t("data.t2_gamma"), 0.01, 0.3, 0.05, 0.01)
        N_pop = st.number_input(t("data.t2_pop"), 1000, 100000, 10000)
        I0 = st.number_input(t("data.t2_i0"), 1, 500, 10)
        days_sim = st.slider(t("data.t2_days"), 30, 365, 180)
        S, I, R = sir_simulation(beta, gamma, N_pop, I0, days_sim)
        fig_sir = go.Figure()
        fig_sir.add_trace(go.Scatter(y=S, mode='lines', name=t("data.t2_legend_s")))
        fig_sir.add_trace(go.Scatter(y=I, mode='lines', name=t("data.t2_legend_i")))
        fig_sir.add_trace(go.Scatter(y=R, mode='lines', name=t("data.t2_legend_r")))
        fig_sir.update_layout(xaxis_title=t("data.t2_xaxis"), yaxis_title=t("data.t2_yaxis"),
                              plot_bgcolor="#111827", paper_bgcolor="#0B1020", font=dict(color="white"))
        st.plotly_chart(fig_sir, use_container_width=True)

    with tab3:
        st.markdown(t("data.t3_heading"))
        st.markdown(f'<p class="section-subtitle">{t("data.t3_subtitle")}</p>', unsafe_allow_html=True)
        prep_coverage = st.slider(t("data.t3_coverage"), 0, 100, 30)
        effectiveness = 0.99
        reduction = prep_coverage / 100 * effectiveness * 0.8  # 粗略估计
        st.metric(t("data.t3_metric"), f"{reduction*100:.1f}%")
        # 简单柱状图
        cov_values = np.arange(0, 101, 10)
        reductions = cov_values / 100 * effectiveness * 0.8
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=cov_values, y=reductions*100, marker_color='#4ade80'))
        fig_bar.update_layout(xaxis_title=t("data.t3_xaxis"), yaxis_title=t("data.t3_yaxis"),
                              plot_bgcolor="#111827", paper_bgcolor="#0B1020", font=dict(color="white"))
        st.plotly_chart(fig_bar, use_container_width=True)

# =========================
# 个人工具页（新增）
# =========================
elif st.session_state.page == '个人工具':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown(t("tools.section_card"), unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([t("tools.tab1"), t("tools.tab2"), t("tools.tab3")])

    with tab1:
        st.markdown(t("tools.t1_heading"))
        st.markdown(t("tools.t1_intro"))
        _tm_opts = t("tools.t1_method_opts")
        exposure_date = st.date_input(t("tools.t1_date"), datetime.today())
        test_method = st.selectbox(t("tools.t1_method"), ["第四代抗原抗体检测", "第三代抗体检测", "核酸检测"], format_func=lambda x: _tm_opts.get(x, x))
        if test_method == "第四代抗原抗体检测":
            window_days = 18
            early_days = 14
        elif test_method == "第三代抗体检测":
            window_days = 30
            early_days = 21
        else:
            window_days = 10
            early_days = 7

        earliest = exposure_date + timedelta(days=early_days)
        reliable = exposure_date + timedelta(days=window_days)
        st.write(t("tools.t1_earliest").format(date=earliest.strftime('%Y-%m-%d')))
        st.write(t("tools.t1_reliable").format(date=reliable.strftime('%Y-%m-%d')))
        st.info(t("tools.t1_note"))

    with tab2:
        st.markdown(t("tools.t2_heading"))
        _dt_opts = t("tools.t2_drug_opts")
        drug_type = st.selectbox(t("tools.t2_drug"), ["TDF/FTC (每日口服)", "TAF/FTC (每日口服)", "长效注射剂"], format_func=lambda x: _dt_opts.get(x, x))
        miss_time = st.number_input(t("tools.t2_miss"), 0, 72, 12)
        if drug_type in ["TDF/FTC (每日口服)", "TAF/FTC (每日口服)"]:
            if miss_time <= 12:
                st.success(t("tools.t2_ok"))
            elif 12 < miss_time <= 24:
                st.warning(t("tools.t2_warn"))
            else:
                st.error(t("tools.t2_err"))
        else:
            st.info(t("tools.t2_inject"))

    with tab3:
        st.markdown(t("tools.t3_heading"))
        st.markdown(t("tools.t3_intro"))
        log_days = st.slider(t("tools.t3_days"), 7, 60, 30)
        default_adherence = [1 if i % 7 != 0 else 0 for i in range(log_days)]  # 模拟漏服
        adherence_input = []
        st.write(t("tools.t3_status_intro"))
        cols = st.columns(7)
        for i in range(log_days):
            with cols[i % 7]:
                default_val = 1 if i % 7 != 0 else 0
                val = st.checkbox(t("tools.t3_day_label").format(n=i + 1), value=bool(default_val), key=f"log_{i}")
                adherence_input.append(1 if val else 0)

        if st.button(t("tools.t3_gen_btn")):
            conc_log = []
            A = 0
            dose_val = 300
            for taken in adherence_input:
                if taken:
                    A += dose_val
                A *= 0.85  # 一级消除近似
                conc_log.append(A)
            fig_log = go.Figure()
            fig_log.add_trace(go.Scatter(y=conc_log, mode='lines+markers', name=t("tools.t3_conc_name")))
            fig_log.add_hline(y=700, line_dash="dot", line_color="red", annotation_text=t("tools.t3_threshold"))
            fig_log.update_layout(xaxis_title=t("tools.t3_xaxis"), yaxis_title=t("tools.t3_yaxis"),
                                  plot_bgcolor="#111827", paper_bgcolor="#0B1020", font=dict(color="white"))
            st.plotly_chart(fig_log, use_container_width=True)
            days_protected = sum(np.array(conc_log) > 700)
            st.metric(t("tools.t3_protected"), f"{days_protected}/{log_days}")

# =========================
# 政策与权益页（新增）
# =========================
elif st.session_state.page == '政策':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown(t("policy.section_card"), unsafe_allow_html=True)

    policy_tabs = st.tabs([t("policy.tab.laws"), t("policy.tab.privacy"), t("policy.tab.antidiscrim")])

    with policy_tabs[0]:
        st.markdown(t("policy.laws_heading"))
        for title, desc in t("policy.laws"):
            st.markdown(f"""
            <div class="card">
            <h4 style="color:#93c5fd;">{title}</h4>
            <p style="color:#cbd5e1;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    with policy_tabs[1]:
        st.markdown(t("policy.privacy_heading"))
        st.markdown(t("policy.privacy_card"), unsafe_allow_html=True)

    with policy_tabs[2]:
        st.markdown(t("policy.anti_heading"))
        st.markdown(t("policy.anti_card"), unsafe_allow_html=True)

# =========================
# 故事与案例页（新增）
# =========================
elif st.session_state.page == '故事':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown(t("story.section_card"), unsafe_allow_html=True)

    for title, content in t("story.list"):
        st.markdown(f"""
        <div class="card">
        <h4 style="color:#60a5fa;">{title}</h4>
        <p style="color:#cbd5e1; line-height:1.8;">{content}</p>
        </div>
        """, unsafe_allow_html=True)

# =========================
# 高级工具页（进阶模型集成；调用 src/ 下的纯模型模块）
# =========================
elif st.session_state.page == '高级工具':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown("""
    <div class="main-card">
        <p class="main-title">🧪 进阶模型工具箱</p>
        <p class="caption-text">
        本页把平台后端的科学模型模块（药代动力学、给药计算、服药依从性、暴露风险、用药安全）
        以交互形式呈现。所有计算均来自 <code>src/</code> 下不依赖界面的纯函数模块，
        已被 <code>tests/unit/</code> 覆盖。结果仅供科普教育，不能替代专业医疗意见。
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not _ADVANCED_MODULES_OK:
        st.error(f"进阶模型模块未能加载：{_ADVANCED_IMPORT_ERR}")
    else:
        adv_tabs = st.tabs([
            "💊 高级药代动力学",
            "⚖️ 给药计算器",
            "📅 服药依从性",
            "⚠️ 暴露风险",
            "🧬 用药安全",
        ])

        # ---------- Tab 1：高级药代动力学 ----------
        with adv_tabs[0]:
            st.markdown("#### 口服一室模型浓度-时间曲线")
            st.caption("基于 Bateman 吸收-消除方程，调节参数观察血药浓度随时间变化。")
            c1, c2, c3 = st.columns(3)
            with c1:
                pk_dose = st.slider("单次剂量 (mg)", 50, 600, 300, 10, key="adv_pk_dose")
                pk_vd = st.slider("分布容积 Vd (L)", 10, 200, 70, 5, key="adv_pk_vd")
            with c2:
                pk_ka = st.slider("吸收速率 ka (1/h)", 0.1, 2.0, 1.0, 0.1, key="adv_pk_ka")
                pk_ke = st.slider("消除速率 ke (1/h)", 0.01, 0.5, 0.1, 0.01, key="adv_pk_ke")
            with c3:
                pk_tau = st.slider("给药间隔 τ (h)", 6, 48, 24, 6, key="adv_pk_tau")
                pk_hours = st.slider("观察时长 (h)", 12, 168, 72, 12, key="adv_pk_hours")
            try:
                t_axis = np.linspace(0, pk_hours, 200)
                conc = _pk_adv.one_compartment_oral(t_axis, pk_dose, pk_vd, pk_ka, pk_ke)
                st.line_chart(np.asarray(conc, dtype=float))
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("达峰时间 Tmax (h)", f"{_pk_adv.tmax_oral(pk_ka, pk_ke):.2f}")
                m2.metric("峰浓度 Cmax", f"{_pk_adv.cmax_oral(pk_dose, pk_vd, pk_ka, pk_ke):.2f}")
                m3.metric("消除半衰期 (h)", f"{_pk_adv.half_life_from_ke(pk_ke):.2f}")
                m4.metric("累积因子", f"{_pk_adv.accumulation_factor(pk_ke, pk_tau):.2f}")
                st.caption(f"达稳态所需时间约 {_pk_adv.time_to_steady_state(pk_ke):.1f} h（达到稳态 95%）。")
            except Exception as e:
                st.warning(f"计算未完成：{e}")

        # ---------- Tab 2：给药计算器 ----------
        with adv_tabs[1]:
            st.markdown("#### 体表面积 / 肾功能与给药调整")
            c1, c2 = st.columns(2)
            with c1:
                dc_height = st.number_input("身高 (cm)", 100.0, 220.0, 170.0, 1.0, key="adv_dc_h")
                dc_weight = st.number_input("体重 (kg)", 30.0, 150.0, 65.0, 1.0, key="adv_dc_w")
                dc_age = st.number_input("年龄 (岁)", 12, 90, 30, 1, key="adv_dc_age")
            with c2:
                dc_scr = st.number_input("血肌酐 (mg/dL)", 0.3, 8.0, 0.9, 0.1, key="adv_dc_scr")
                dc_female = st.checkbox("女性", value=False, key="adv_dc_sex")
            try:
                bsa = _dose.mosteller_bsa(dc_height, dc_weight)
                crcl = _dose.cockcroft_gault_crcl(dc_age, dc_weight, dc_scr, is_female=dc_female)
                egfr = _dose.ckd_epi_egfr(dc_age, dc_scr, is_female=dc_female)
                m1, m2, m3 = st.columns(3)
                m1.metric("体表面积 BSA (m²)", f"{bsa:.2f}")
                m2.metric("肌酐清除率 (mL/min)", f"{crcl:.1f}")
                m3.metric("eGFR (mL/min/1.73m²)", f"{egfr:.1f}")
                st.info(f"肾功能分期：{_dose.renal_function_stage(egfr)}")
                st.info(f"TDF 给药建议：{_dose.tdf_renal_dose_interval(crcl)}")
                st.info(f"PrEP 肾功能准入：{_dose.prep_renal_eligibility(crcl)}")
                st.markdown("##### 按需 PrEP（2-1-1 方案）服药时间表")
                st.write(_dose.prep_on_demand_211_schedule())
            except Exception as e:
                st.warning(f"计算未完成：{e}")

        # ---------- Tab 3：服药依从性 ----------
        with adv_tabs[2]:
            st.markdown("#### 依从性对保护效果的影响")
            c1, c2 = st.columns(2)
            with c1:
                adh_days = st.slider("观察天数", 14, 90, 30, 1, key="adv_adh_days")
                adh_missprob = st.slider("每日漏服概率", 0.0, 0.6, 0.15, 0.05, key="adv_adh_miss")
            with c2:
                adh_seed = st.number_input("随机种子", 0, 9999, 42, 1, key="adv_adh_seed")
            try:
                log = _adh.simulate_random_missing(adh_days, adh_missprob, seed=int(adh_seed))
                pdc = _adh.proportion_days_covered(log, adh_days)
                m1, m2, m3 = st.columns(3)
                m1.metric("依从率 PDC", f"{pdc*100:.0f}%")
                m2.metric("保护概率", f"{_adh.protection_from_adherence(pdc)*100:.0f}%")
                m3.metric("依从分层", f"{_adh.adherence_tier(pdc)}")
                st.markdown("##### 服药记录（1=服药，0=漏服）")
                st.bar_chart(np.asarray(log, dtype=float))
                st.markdown("##### 依从率 → 保护概率曲线")
                rates = np.linspace(0, 1, 21)
                curve = _adh.adherence_protection_curve(rates)
                st.line_chart(np.asarray(curve, dtype=float))
                with st.expander("完整依从性摘要"):
                    st.json(_adh.summarize_adherence(log, adh_days))
            except Exception as e:
                st.warning(f"计算未完成：{e}")

        # ---------- Tab 4：暴露风险 ----------
        with adv_tabs[3]:
            st.markdown("#### 单次暴露 / 时间窗累积风险")
            exposure_map = {
                "接受性肛交": "receptive_anal",
                "插入性肛交": "insertive_anal",
                "阴道性交": "vaginal",
                "口交": "oral",
            }
            c1, c2 = st.columns(2)
            with c1:
                rk_label = st.selectbox("暴露类型", list(exposure_map.keys()), key="adv_rk_type")
                rk_condom = st.checkbox("使用安全套", value=False, key="adv_rk_condom")
            with c2:
                rk_suppressed = st.checkbox("伴侣病毒已抑制 (U=U)", value=False, key="adv_rk_supp")
                rk_n = st.slider("暴露次数", 1, 100, 10, 1, key="adv_rk_n")
            try:
                etype = exposure_map[rk_label]
                single = _risk.per_act_risk(etype, condom_use=rk_condom, partner_suppressed=rk_suppressed)
                window = _risk.time_window_risk(etype, rk_n, condom_use=rk_condom, partner_suppressed=rk_suppressed)
                m1, m2 = st.columns(2)
                m1.metric("单次暴露风险", f"{single*100:.4f}%")
                m2.metric(f"{rk_n} 次累积风险", f"{window*100:.3f}%")
                st.caption("累积风险按 1−∏(1−pᵢ) 计算，随暴露次数增加而单调上升。")
                ns = np.arange(1, rk_n + 1)
                cum = [_risk.cumulative_risk_repeated(single, int(k)) for k in ns]
                st.line_chart(np.asarray(cum, dtype=float))
            except Exception as e:
                st.warning(f"计算未完成：{e}")

        # ---------- Tab 5：用药安全 ----------
        with adv_tabs[4]:
            st.markdown("#### 药物相互作用检查")
            drug_choices = ["TDF", "TAF", "FTC", "DTG", "CAB", "利福平", "布洛芬", "庆大霉素", "二甲双胍", "卡马西平"]
            picked = st.multiselect("选择当前用药方案", drug_choices, default=["TDF", "FTC", "利福平"], key="adv_ddi")
            if picked:
                try:
                    review = _ddi.review_regimen(picked)
                    st.json(review)
                except Exception as e:
                    st.warning(f"相互作用检查未完成：{e}")
            st.markdown("---")
            st.markdown("#### 化验指标解读")
            c1, c2, c3 = st.columns(3)
            with c1:
                lab_cd4 = st.number_input("CD4 (cells/µL)", 0, 2000, 450, 10, key="adv_lab_cd4")
            with c2:
                lab_vl = st.number_input("病毒载量 (copies/mL)", 0, 10_000_000, 20000, 1000, key="adv_lab_vl")
            with c3:
                lab_alt = st.number_input("ALT (U/L)", 0, 1000, 35, 5, key="adv_lab_alt")
            try:
                st.write("CD4 解读：", _lab.interpret_cd4(lab_cd4))
                st.write("病毒载量解读：", _lab.interpret_viral_load(lab_vl))
                st.write("ALT 分级：", _lab.grade_alt(lab_alt))
            except Exception as e:
                st.warning(f"化验解读未完成：{e}")

# =========================
# 知识库与流行病学页
# =========================
elif st.session_state.page == '知识库':
    if st.button(t("common.back_home")):
        go_to('home')

    st.markdown("""
    <div class="main-card">
        <p class="main-title">📚 知识库与流行病学</p>
        <p class="caption-text">
        术语检索、群体传播模拟、病毒动力学与卫生经济学分析。
        模型来自 <code>src/</code> 下可独立测试的纯函数模块，结果仅供教育用途。
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not _ADVANCED_MODULES_OK:
        st.error(f"进阶模型模块未能加载：{_ADVANCED_IMPORT_ERR}")
    else:
        kb_tabs = st.tabs([
            "🔍 术语检索",
            "🦠 流行病学模拟",
            "🧬 病毒动力学",
            "💰 卫生经济学",
            "📈 统计分析",
        ])

        # ---------- Tab 1：术语检索 ----------
        with kb_tabs[0]:
            st.markdown("#### HIV 预防术语 / FAQ 检索")
            query = st.text_input("输入关键词（如 PrEP、窗口期、U=U）", "PrEP", key="kb_query")
            try:
                if query.strip():
                    hits = _know.search_glossary(query, limit=5)
                    if hits:
                        for item in hits:
                            st.markdown(f"<div class='card'><h4 style='color:#60a5fa;'>{item}</h4></div>",
                                        unsafe_allow_html=True)
                    else:
                        st.info("未找到匹配术语，换个关键词试试。")
                st.markdown("##### 涵盖主题")
                st.write(_know.list_topics())
                st.markdown("##### 随机科普小贴士")
                for tip in _know.random_tips(3, seed=int(np.random.randint(0, 9999))):
                    st.success(tip)
            except Exception as e:
                st.warning(f"检索未完成：{e}")

        # ---------- Tab 2：流行病学模拟 ----------
        with kb_tabs[1]:
            st.markdown("#### SEIR 群体传播模拟")
            c1, c2, c3 = st.columns(3)
            with c1:
                ep_beta = st.slider("传播率 β", 0.05, 1.0, 0.3, 0.05, key="kb_beta")
                ep_sigma = st.slider("潜伏转化率 σ", 0.05, 1.0, 0.2, 0.05, key="kb_sigma")
            with c2:
                ep_gamma = st.slider("康复率 γ", 0.02, 0.5, 0.1, 0.02, key="kb_gamma")
                ep_days = st.slider("模拟天数", 30, 365, 160, 10, key="kb_days")
            with c3:
                ep_N = st.number_input("总人口 N", 100, 1_000_000, 10000, 100, key="kb_N")
                ep_I0 = st.number_input("初始感染 I0", 1, 1000, 10, 1, key="kb_I0")
            try:
                S, E, I, R = _epi.seir_simulation(ep_beta, ep_sigma, ep_gamma, ep_N, ep_I0, ep_days)
                chart_data = {
                    "易感 S": np.asarray(S, dtype=float),
                    "潜伏 E": np.asarray(E, dtype=float),
                    "感染 I": np.asarray(I, dtype=float),
                    "康复 R": np.asarray(R, dtype=float),
                }
                st.line_chart(chart_data)
                R0 = _epi.basic_reproduction_number(ep_beta, ep_gamma)
                m1, m2 = st.columns(2)
                m1.metric("基本再生数 R₀", f"{R0:.2f}")
                m2.metric("群体免疫阈值", f"{_epi.herd_immunity_threshold(R0)*100:.0f}%")
            except Exception as e:
                st.warning(f"模拟未完成：{e}")

        # ---------- Tab 3：病毒动力学 ----------
        with kb_tabs[2]:
            st.markdown("#### ART 治疗后病毒载量双相衰减")
            c1, c2 = st.columns(2)
            with c1:
                vd_v0 = st.number_input("初始病毒载量 (copies/mL)", 1000, 10_000_000, 100000, 1000, key="kb_v0")
                vd_days = st.slider("观察天数", 7, 180, 60, 1, key="kb_vddays")
            with c2:
                vd_kfast = st.slider("快相衰减率", 0.1, 1.0, 0.5, 0.05, key="kb_kfast")
                vd_kslow = st.slider("慢相衰减率", 0.01, 0.2, 0.05, 0.01, key="kb_kslow")
            try:
                t_days = np.arange(0, vd_days + 1)
                V = _vd.art_biphasic_decay(t_days, V0=vd_v0, k_fast=vd_kfast, k_slow=vd_kslow)
                st.line_chart(np.asarray(_vd.viral_load_to_log10(np.maximum(V, 1.0)), dtype=float))
                st.caption("纵轴为 log10(病毒载量)。")
                ttu = _vd.time_to_undetectable(V0=vd_v0, k_fast=vd_kfast, k_slow=vd_kslow)
                st.metric("预计达检测限以下天数", f"{ttu:.0f}")
            except Exception as e:
                st.warning(f"计算未完成：{e}")

        # ---------- Tab 4：卫生经济学 ----------
        with kb_tabs[3]:
            st.markdown("#### PrEP 项目成本效益（简化）")
            c1, c2 = st.columns(2)
            with c1:
                ce_cost = st.number_input("人均年成本 (元)", 0, 100000, 8000, 500, key="kb_cost")
                ce_n = st.number_input("覆盖人数", 1, 100000, 1000, 10, key="kb_n")
            with c2:
                ce_incidence = st.slider("基线年发病率", 0.001, 0.1, 0.02, 0.001, key="kb_inc")
                ce_eff = st.slider("PrEP 有效性", 0.5, 0.99, 0.9, 0.01, key="kb_eff")
            try:
                averted = _cea.infections_averted(ce_incidence, ce_eff, ce_n, years=1.0)["averted"]
                total_cost = _cea.program_cost(ce_cost, ce_n, years=1.0)
                cpia = _cea.cost_per_infection_averted(total_cost, averted)
                m1, m2, m3 = st.columns(3)
                m1.metric("避免感染数", f"{averted:.1f}")
                m2.metric("项目总成本 (元)", f"{total_cost:,.0f}")
                m3.metric("每避免一例成本 (元)", f"{cpia:,.0f}")
            except Exception as e:
                st.warning(f"计算未完成：{e}")

        # ---------- Tab 5：统计分析 ----------
        with kb_tabs[4]:
            st.markdown("#### 描述性统计")
            raw = st.text_area("输入一组数值（逗号或空格分隔）", "12, 15, 14, 10, 18, 21, 13, 16", key="kb_stats")
            try:
                import re as _re
                nums = [float(x) for x in _re.split(r"[,\s]+", raw.strip()) if x]
                if nums:
                    st.json(_stats.describe(nums))
                    lo, hi = _stats.mean_confidence_interval(nums)
                    st.caption(f"均值 95% 置信区间：[{lo:.2f}, {hi:.2f}]")
            except Exception as e:
                st.warning(f"统计未完成：{e}")

# 侧边栏永久展示平台说明（所有页面都显示）
st.sidebar.markdown(t("sidebar.title"))
st.sidebar.info(t("sidebar.info"))

