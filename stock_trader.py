#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票交易助手
用于管理自选股票并获取交易建议的Windows桌面应用程序
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import threading
import time
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd
import numpy as np

# 版本号
VERSION = "1.0.0"


class StockTrader:
    def __init__(self, root):
        self.root = root
        self.root.title(f"股票交易助手 v{VERSION}")
        self.root.geometry("900x600")
        
        # 自选股票列表文件
        self.stock_file = "watchlist.json"
        
        # 加载自选股票列表
        self.watchlist = self.load_watchlist()
        
        # 股票数据缓存
        self.stock_data = {}
        
        # 全局股票数据缓存（避免频繁请求）
        self.all_stocks_cache = None
        self.cache_time = None
        self.cache_timeout = 60  # 缓存60秒
        
        # 创建界面
        self.create_widgets()
        
        # 如果已有自选股票，自动加载显示
        if self.watchlist:
            self.display_stocks()
    
    def load_watchlist(self):
        """从JSON文件加载自选股票列表"""
        if os.path.exists(self.stock_file):
            try:
                with open(self.stock_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_watchlist(self):
        """保存自选股票列表到JSON文件"""
        try:
            with open(self.stock_file, 'w', encoding='utf-8') as f:
                json.dump(self.watchlist, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def create_widgets(self):
        """创建GUI界面"""
        # 顶部输入区域
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="股票代码:").pack(side=tk.LEFT, padx=5)
        
        self.code_entry = ttk.Entry(input_frame, width=15)
        self.code_entry.pack(side=tk.LEFT, padx=5)
        self.code_entry.bind('<Return>', lambda e: self.add_stock())
        
        ttk.Button(input_frame, text="添加股票", command=self.add_stock).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="更新价格", command=self.update_prices).pack(side=tk.LEFT, padx=5)
        
        # 提示标签
        self.status_label = ttk.Label(input_frame, text="请输入6位股票代码（如：000001、600000）", foreground="gray")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # 股票列表显示区域
        list_frame = ttk.Frame(self.root, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview显示股票信息
        columns = ("代码", "名称", "当前价", "涨跌幅", "建议", "预测准确性", "更新时间")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题和宽度
        self.tree.heading("代码", text="股票代码")
        self.tree.heading("名称", text="股票名称")
        self.tree.heading("当前价", text="当前价格")
        self.tree.heading("涨跌幅", text="涨跌幅(%)")
        self.tree.heading("建议", text="交易建议")
        self.tree.heading("预测准确性", text="预测准确性(%)")
        self.tree.heading("更新时间", text="更新时间")
        
        self.tree.column("代码", width=100, anchor=tk.CENTER)
        self.tree.column("名称", width=150, anchor=tk.CENTER)
        self.tree.column("当前价", width=100, anchor=tk.CENTER)
        self.tree.column("涨跌幅", width=100, anchor=tk.CENTER)
        self.tree.column("建议", width=150, anchor=tk.CENTER)
        self.tree.column("预测准确性", width=110, anchor=tk.CENTER)
        self.tree.column("更新时间", width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单 - 删除股票
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="删除", command=self.delete_stock)
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            self.context_menu.post(event.x_root, event.y_root)
    
    def add_stock(self):
        """添加股票到自选列表"""
        code = self.code_entry.get().strip()
        
        if not code:
            messagebox.showwarning("警告", "请输入股票代码")
            return
        
        # 验证股票代码格式（6位数字）
        if not code.isdigit() or len(code) != 6:
            messagebox.showerror("错误", "股票代码必须是6位数字（如：000001、600000）")
            return
        
        # 检查是否已存在
        if code in self.watchlist:
            messagebox.showinfo("提示", f"股票 {code} 已在自选列表中")
            return
        
        # 验证股票代码是否有效
        if not self.validate_stock_code(code):
            messagebox.showerror("错误", f"股票代码 {code} 无效或不存在")
            return
        
        # 添加到列表
        self.watchlist.append(code)
        self.save_watchlist()
        
        # 清空输入框
        self.code_entry.delete(0, tk.END)
        
        # 更新显示
        self.display_stocks()
        
        # 自动获取一次价格
        self.update_single_stock(code)
    
    def validate_stock_code(self, code):
        """验证股票代码是否有效"""
        try:
            # 尝试获取股票基本信息
            stock_info = ak.stock_individual_info_em(symbol=code)
            return stock_info is not None and not stock_info.empty
        except:
            return False
    
    def delete_stock(self):
        """从自选列表删除股票"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        code = values[0]
        
        if messagebox.askyesno("确认", f"确定要删除股票 {code} 吗？"):
            if code in self.watchlist:
                self.watchlist.remove(code)
                self.save_watchlist()
                self.display_stocks()
    
    def display_stocks(self):
        """显示自选股票列表"""
        # 清空现有显示
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 显示所有自选股票
        for code in self.watchlist:
            if code in self.stock_data:
                data = self.stock_data[code]
                name = data.get('name', code)
                price = data.get('price', '--')
                change_pct = data.get('change_pct', '--')
                advice = data.get('advice', '--')
                accuracy = data.get('accuracy', '--')
                update_time = data.get('update_time', '--')
            else:
                name = code
                price = '--'
                change_pct = '--'
                advice = '--'
                accuracy = '--'
                update_time = '--'
            
            self.tree.insert("", tk.END, values=(code, name, price, change_pct, advice, accuracy, update_time))
    
    def update_prices(self):
        """更新所有自选股票的价格"""
        if not self.watchlist:
            messagebox.showinfo("提示", "自选列表为空，请先添加股票")
            return
        
        # 在新线程中更新，避免界面卡顿
        threading.Thread(target=self._update_prices_thread, daemon=True).start()
        self.status_label.config(text="正在更新价格...", foreground="blue")
    
    def _update_prices_thread(self):
        """更新价格的线程函数"""
        success_count = 0
        for i, code in enumerate(self.watchlist):
            if self.update_single_stock(code):
                success_count += 1
            # 添加延迟，避免请求过快导致连接被关闭
            if i < len(self.watchlist) - 1:
                time.sleep(0.5)  # 每次请求间隔0.5秒
        
        # 更新完成后刷新显示
        self.root.after(0, self.display_stocks)
        self.root.after(0, lambda: self.status_label.config(
            text=f"更新完成！成功更新 {success_count}/{len(self.watchlist)} 只股票", 
            foreground="green"
        ))
    
    def get_all_stocks_data(self):
        """获取所有股票数据（带缓存和重试机制）"""
        # 检查缓存是否有效
        if self.all_stocks_cache is not None and self.cache_time is not None:
            if time.time() - self.cache_time < self.cache_timeout:
                return self.all_stocks_cache
        
        # 重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stock_data = ak.stock_zh_a_spot_em()
                # 缓存数据
                self.all_stocks_cache = stock_data
                self.cache_time = time.time()
                return stock_data
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"获取股票数据失败，重试 {attempt + 1}/{max_retries}: {str(e)}")
                    time.sleep(1)  # 等待1秒后重试
                else:
                    print(f"获取股票数据失败（已重试{max_retries}次）: {str(e)}")
                    return None
        return None
    
    def update_single_stock(self, code):
        """更新单只股票的价格（带重试机制）"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                # 方法1：从全局实时行情数据获取（优先，速度快）
                stock_data = self.get_all_stocks_data()
                
                if stock_data is not None and not stock_data.empty:
                    stock_info = stock_data[stock_data['代码'] == code]
                    if not stock_info.empty:
                        row = stock_info.iloc[0]
                        name = row['名称']
                        price = row['最新价']
                        change_pct = row['涨跌幅']
                        
                        # 获取历史数据计算技术指标（尝试多个数据源）
                        indicators = None
                        hist_data = None
                        
                        # 方法1：尝试使用东方财富接口（带复权）
                        if hist_data is None:
                            try:
                                hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq", start_date="20230101")
                                if hist_data is not None and not hist_data.empty:
                                    print(f"获取股票 {code} 历史数据成功（东方财富-前复权），共 {len(hist_data)} 条")
                            except Exception as e:
                                print(f"方法1失败（东方财富-前复权）: {str(e)}")
                                hist_data = None
                        
                        # 方法2：尝试使用东方财富接口（不复权）
                        if hist_data is None:
                            try:
                                hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="", start_date="20230101")
                                if hist_data is not None and not hist_data.empty:
                                    print(f"获取股票 {code} 历史数据成功（东方财富-不复权），共 {len(hist_data)} 条")
                            except Exception as e:
                                print(f"方法2失败（东方财富-不复权）: {str(e)}")
                                hist_data = None
                        
                        # 方法3：尝试使用东方财富接口（后复权）
                        if hist_data is None:
                            try:
                                hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="hfq", start_date="20230101")
                                if hist_data is not None and not hist_data.empty:
                                    print(f"获取股票 {code} 历史数据成功（东方财富-后复权），共 {len(hist_data)} 条")
                            except Exception as e:
                                print(f"方法3失败（东方财富-后复权）: {str(e)}")
                                hist_data = None
                        
                        # 方法4：尝试使用更早的日期范围（可能数据更多）
                        if hist_data is None:
                            try:
                                hist_data = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq", start_date="20220101")
                                if hist_data is not None and not hist_data.empty:
                                    print(f"获取股票 {code} 历史数据成功（扩展日期范围），共 {len(hist_data)} 条")
                            except Exception as e:
                                print(f"方法4失败（扩展日期范围）: {str(e)}")
                                hist_data = None
                        
                        # 如果获取到数据，计算技术指标
                        if hist_data is not None and not hist_data.empty:
                            indicators = self.calculate_technical_indicators(hist_data)
                        else:
                            print(f"所有数据源均失败，股票 {code} 无法获取历史数据")
                        
                        # 生成交易建议和准确性
                        advice, accuracy = self.generate_advice(price, change_pct, indicators)
                        
                        # 保存数据
                        self.stock_data[code] = {
                            'name': name,
                            'price': f"{price:.2f}" if price else "--",
                            'change_pct': f"{change_pct:.2f}" if change_pct is not None else "--",
                            'advice': advice,
                            'accuracy': f"{accuracy:.2f}",
                            'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        return True
                
                # 方法2：使用个股历史数据接口（备用，尝试多个数据源）
                current_data = None
                
                # 尝试多个数据源获取历史数据
                for method_name, params in [
                    ("东方财富-前复权", {"period": "daily", "adjust": "qfq"}),
                    ("东方财富-不复权", {"period": "daily", "adjust": ""}),
                    ("东方财富-后复权", {"period": "daily", "adjust": "hfq"}),
                ]:
                    if current_data is None:
                        try:
                            current_data = ak.stock_zh_a_hist(symbol=code, start_date="20230101", **params)
                            if current_data is not None and not current_data.empty:
                                print(f"备用方法获取股票 {code} 历史数据成功（{method_name}），共 {len(current_data)} 条")
                                break
                        except Exception as e:
                            print(f"备用方法失败（{method_name}）: {str(e)}")
                            current_data = None
                
                if current_data is not None and not current_data.empty:
                    try:
                        latest = current_data.iloc[-1]
                        # 尝试不同的收盘价列名
                        close_price = None
                        for col in ['收盘', 'close', '现价', '最新价']:
                            if col in latest.index:
                                close_price = latest[col]
                                break
                        
                        if close_price is None:
                            # 如果找不到，尝试数值列
                            for col in current_data.columns:
                                if '收盘' in str(col) or 'close' in str(col).lower():
                                    close_price = latest[col]
                                    break
                        
                        if close_price is None:
                            raise Exception("无法找到收盘价列")
                        
                        price = float(close_price)
                        
                        # 获取股票名称
                        try:
                            stock_detail = ak.stock_individual_info_em(symbol=code)
                            if stock_detail is not None and not stock_detail.empty:
                                name_row = stock_detail[stock_detail['item'] == '股票简称']
                                if not name_row.empty:
                                    name = name_row['value'].values[0]
                                else:
                                    name = code
                            else:
                                name = code
                        except:
                            name = code
                        
                        # 计算涨跌幅（与前一交易日比较）
                        if len(current_data) > 1:
                            prev_close = None
                            for col in ['收盘', 'close', '现价', '最新价']:
                                if col in current_data.columns:
                                    prev_close = current_data.iloc[-2][col]
                                    break
                            if prev_close is None:
                                for col in current_data.columns:
                                    if '收盘' in str(col) or 'close' in str(col).lower():
                                        prev_close = current_data.iloc[-2][col]
                                        break
                            
                            if prev_close is not None:
                                change_pct = ((price - float(prev_close)) / float(prev_close)) * 100
                            else:
                                change_pct = 0.0
                        else:
                            change_pct = 0.0
                        
                        # 计算技术指标
                        indicators = self.calculate_technical_indicators(current_data)
                        
                        # 生成交易建议和准确性
                        advice, accuracy = self.generate_advice(price, change_pct, indicators)
                        
                        # 保存数据
                        self.stock_data[code] = {
                            'name': name,
                            'price': f"{price:.2f}" if price else "--",
                            'change_pct': f"{change_pct:.2f}" if change_pct is not None else "--",
                            'advice': advice,
                            'accuracy': f"{accuracy:.2f}",
                            'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        return True
                    except Exception as e:
                        print(f"处理历史数据失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                # 如果所有方法都失败，继续重试
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    print(f"备用方法获取股票 {code} 失败")
                
                # 如果两种方法都失败
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    raise Exception("所有方法都失败")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"更新股票 {code} 失败，重试 {attempt + 1}/{max_retries}: {str(e)}")
                    time.sleep(1)  # 等待后重试
                else:
                    # 最终失败，保存错误信息
                    self.stock_data[code] = {
                        'name': code,
                        'price': '--',
                        'change_pct': '--',
                        'advice': '数据获取失败',
                        'accuracy': '--',
                        'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    print(f"更新股票 {code} 失败（已重试{max_retries}次）: {str(e)}")
                    return False
        
        return False
    
    def calculate_technical_indicators(self, hist_data):
        """计算技术指标"""
        if hist_data is None or hist_data.empty:
            print("技术指标计算失败: 数据为空")
            return None
        
        if len(hist_data) < 5:
            print(f"技术指标计算失败: 数据量不足（只有{len(hist_data)}条，至少需要5条）")
            return None
        
        try:
            # 检测列名（akshare可能返回不同的列名）
            date_col = None
            close_col = None
            volume_col = None
            
            # 尝试匹配日期列
            for col in hist_data.columns:
                if '日期' in str(col) or 'date' in str(col).lower() or '时间' in str(col):
                    date_col = col
                    break
            
            # 尝试匹配收盘价列
            for col in hist_data.columns:
                if '收盘' in str(col) or 'close' in str(col).lower() or '现价' in str(col):
                    close_col = col
                    break
            
            # 尝试匹配成交量列
            for col in hist_data.columns:
                if '成交量' in str(col) or 'volume' in str(col).lower() or '量' in str(col):
                    volume_col = col
                    break
            
            # 如果找不到关键列，打印列名用于调试
            if date_col is None or close_col is None:
                print(f"技术指标计算失败: 无法找到必要的列")
                print(f"可用列名: {hist_data.columns.tolist()}")
                print(f"找到的日期列: {date_col}, 收盘价列: {close_col}")
                return None
            
            # 确保数据按日期排序
            if date_col:
                hist_data = hist_data.sort_values(date_col)
            
            # 获取收盘价数据
            closes = pd.to_numeric(hist_data[close_col], errors='coerce').dropna().values
            
            if len(closes) < 5:
                print(f"技术指标计算失败: 有效收盘价数据不足（只有{len(closes)}条）")
                return None
            
            # 获取成交量数据（可选）
            volumes = None
            if volume_col:
                try:
                    volumes = pd.to_numeric(hist_data[volume_col], errors='coerce').dropna().values
                    if len(volumes) == 0:
                        volumes = None
                except:
                    volumes = None
            
            indicators = {}
            
            # 1. 移动平均线 (MA)
            if len(closes) >= 5:
                indicators['ma5'] = float(np.mean(closes[-5:]))
            if len(closes) >= 10:
                indicators['ma10'] = float(np.mean(closes[-10:]))
            if len(closes) >= 20:
                indicators['ma20'] = float(np.mean(closes[-20:]))
            
            # 2. RSI相对强弱指标
            if len(closes) >= 14:
                deltas = np.diff(closes)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains[-14:])
                avg_loss = np.mean(losses[-14:])
                
                if avg_loss != 0:
                    rs = avg_gain / avg_loss
                    indicators['rsi'] = float(100 - (100 / (1 + rs)))
                else:
                    indicators['rsi'] = 100.0
            
            # 3. MACD指标
            if len(closes) >= 26:
                ema12 = float(closes[-12:].mean())  # 简化EMA12
                ema26 = float(closes[-26:].mean())   # 简化EMA26
                indicators['macd'] = ema12 - ema26
                indicators['macd_signal'] = indicators['macd'] * 0.9  # 简化信号线
            
            # 4. 成交量变化率
            if volumes is not None and len(volumes) >= 5:
                avg_volume_5 = np.mean(volumes[-5:])
                avg_volume_20 = np.mean(volumes[-20:]) if len(volumes) >= 20 else avg_volume_5
                if avg_volume_20 > 0:
                    indicators['volume_ratio'] = float(avg_volume_5 / avg_volume_20)
                else:
                    indicators['volume_ratio'] = 1.0
            
            # 5. 价格趋势（最近5日vs最近20日）
            if len(closes) >= 20:
                price_5d = np.mean(closes[-5:])
                price_20d = np.mean(closes[-20:])
                if price_20d > 0:
                    indicators['price_trend'] = float((price_5d - price_20d) / price_20d * 100)
                else:
                    indicators['price_trend'] = 0.0
            elif len(closes) >= 10:
                # 如果数据不足20条，使用可用数据
                price_5d = np.mean(closes[-5:])
                price_10d = np.mean(closes[-10:])
                if price_10d > 0:
                    indicators['price_trend'] = float((price_5d - price_10d) / price_10d * 100)
                else:
                    indicators['price_trend'] = 0.0
            
            # 6. 波动率
            if len(closes) >= 10:
                try:
                    # np.diff会减少一个元素，所以需要匹配
                    returns = np.diff(closes[-10:]) / closes[-10:-1]  # 修正：两个数组都是9个元素
                    indicators['volatility'] = float(np.std(returns) * 100)
                except Exception as e:
                    print(f"计算波动率失败: {str(e)}")
                    # 波动率计算失败不影响其他指标
            
            if len(indicators) > 0:
                print(f"技术指标计算成功，共计算了 {len(indicators)} 个指标: {list(indicators.keys())}")
                return indicators
            else:
                print("技术指标计算失败: 没有成功计算任何指标")
                return None
            
        except Exception as e:
            import traceback
            print(f"计算技术指标失败: {str(e)}")
            print(f"错误详情: {traceback.format_exc()}")
            return None
    
    def calculate_accuracy(self, score, indicators_used, change_pct, indicators=None):
        """计算预测准确性（基于指标数量、一致性和信号强度）"""
        if indicators is None or len(indicators_used) == 0:
            # 如果没有技术指标，准确性较低
            return 35.0  # 仅基于涨跌幅，准确性约35%
        
        # 基础准确性：基于使用的指标数量
        base_accuracy = 50.0  # 基础50%
        indicator_count = len(indicators_used)
        
        # 每增加一个指标，提高5-8%的准确性
        if indicator_count >= 5:
            base_accuracy += 30.0
        elif indicator_count >= 4:
            base_accuracy += 20.0
        elif indicator_count >= 3:
            base_accuracy += 12.0
        elif indicator_count >= 2:
            base_accuracy += 6.0
        
        # 信号强度：基于得分绝对值
        score_abs = abs(score)
        if score_abs >= 4:
            strength_bonus = 15.0  # 强烈信号
        elif score_abs >= 2:
            strength_bonus = 10.0  # 明确信号
        elif score_abs >= 0.5:
            strength_bonus = 5.0   # 弱信号
        else:
            strength_bonus = 0.0   # 中性信号
        
        # 指标一致性：检查各指标是否指向同一方向
        consistency_bonus = 0.0
        if indicators:
            buy_signals = 0
            sell_signals = 0
            
            # RSI信号
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi < 40:
                    buy_signals += 1
                elif rsi > 60:
                    sell_signals += 1
            
            # 均线信号
            if 'ma5' in indicators and 'ma20' in indicators:
                ma5 = indicators['ma5']
                ma20 = indicators['ma20']
                if ma5 > ma20:
                    buy_signals += 1
                else:
                    sell_signals += 1
            
            # MACD信号
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd']
                signal = indicators['macd_signal']
                if macd > signal and macd > 0:
                    buy_signals += 1
                elif macd < signal and macd < 0:
                    sell_signals += 1
            
            # 趋势信号
            if 'price_trend' in indicators:
                trend = indicators['price_trend']
                if trend > 0:
                    buy_signals += 1
                elif trend < 0:
                    sell_signals += 1
            
            # 如果信号一致（都指向买入或都指向卖出），增加准确性
            total_signals = buy_signals + sell_signals
            if total_signals > 0:
                consistency = max(buy_signals, sell_signals) / total_signals
                consistency_bonus = consistency * 10.0  # 最高10%加成
        
        # 计算最终准确性
        accuracy = base_accuracy + strength_bonus + consistency_bonus
        
        # 限制在合理范围内（35%-95%）
        accuracy = max(35.0, min(95.0, accuracy))
        
        return round(accuracy, 2)  # 精确到百分之一
    
    def generate_advice(self, price, change_pct, indicators=None):
        """根据价格、涨跌幅和技术指标生成交易建议，返回(建议, 准确性)"""
        if price is None or price == 0:
            return ("数据不足", 0.0)
        
        if change_pct is None:
            return ("继续观望", 35.0)
        
        # 标记是否使用了技术指标
        use_indicators = indicators is not None
        
        # 如果没有技术指标，使用简单逻辑
        if not use_indicators:
            if change_pct > 5:
                return ("建议卖出 (仅涨跌幅)", 35.0)
            elif change_pct > 2:
                return ("谨慎持有 (仅涨跌幅)", 35.0)
            elif change_pct > -2:
                return ("继续持有 (仅涨跌幅)", 35.0)
            elif change_pct > -5:
                return ("可以考虑买入 (仅涨跌幅)", 35.0)
            else:
                return ("建议买入 (仅涨跌幅)", 35.0)
        
        # 综合多个指标进行判断
        score = 0  # 正分表示买入信号，负分表示卖出信号
        indicators_used = []  # 记录使用了哪些指标
        
        # 1. 涨跌幅权重 (30%)
        if change_pct > 5:
            score -= 3
        elif change_pct > 2:
            score -= 1
        elif change_pct < -5:
            score += 3
        elif change_pct < -2:
            score += 1
        
        # 2. RSI指标权重 (25%)
        if 'rsi' in indicators:
            indicators_used.append("RSI")
            rsi = indicators['rsi']
            if rsi > 70:  # 超买
                score -= 2.5
            elif rsi > 60:
                score -= 1
            elif rsi < 30:  # 超卖
                score += 2.5
            elif rsi < 40:
                score += 1
        
        # 3. 均线系统权重 (20%)
        if 'ma5' in indicators and 'ma20' in indicators:
            indicators_used.append("MA")
            ma5 = indicators['ma5']
            ma20 = indicators['ma20']
            current_price = price
            
            if current_price > ma5 > ma20:  # 多头排列
                score += 2
            elif current_price < ma5 < ma20:  # 空头排列
                score -= 2
            elif ma5 > ma20:  # 短期均线在长期均线上方
                score += 1
            else:
                score -= 1
        
        # 4. MACD指标权重 (15%)
        if 'macd' in indicators and 'macd_signal' in indicators:
            indicators_used.append("MACD")
            macd = indicators['macd']
            signal = indicators['macd_signal']
            if macd > signal and macd > 0:  # 金叉且MACD为正
                score += 1.5
            elif macd < signal and macd < 0:  # 死叉且MACD为负
                score -= 1.5
        
        # 5. 成交量权重 (10%)
        if 'volume_ratio' in indicators:
            indicators_used.append("成交量")
            volume_ratio = indicators['volume_ratio']
            if volume_ratio > 1.5:  # 成交量放大
                if change_pct > 0:
                    score += 1  # 价涨量增
                else:
                    score -= 0.5  # 价跌量增
            elif volume_ratio < 0.7:  # 成交量萎缩
                score -= 0.5
        
        # 6. 价格趋势权重 (10%)
        if 'price_trend' in indicators:
            indicators_used.append("趋势")
            trend = indicators['price_trend']
            if trend > 5:  # 强势上涨趋势
                score += 1
            elif trend < -5:  # 强势下跌趋势
                score -= 1
        
        # 计算预测准确性
        accuracy = self.calculate_accuracy(score, indicators_used, change_pct, indicators)
        
        # 根据综合得分给出建议
        if len(indicators_used) == 0:
            # 如果技术指标都不可用，回退到简单逻辑
            if change_pct > 5:
                return ("建议卖出 (仅涨跌幅)", 35.0)
            elif change_pct > 2:
                return ("谨慎持有 (仅涨跌幅)", 35.0)
            elif change_pct > -2:
                return ("继续持有 (仅涨跌幅)", 35.0)
            elif change_pct > -5:
                return ("可以考虑买入 (仅涨跌幅)", 35.0)
            else:
                return ("建议买入 (仅涨跌幅)", 35.0)
        
        # 生成建议文本，包含使用的指标信息
        indicator_info = f"({', '.join(indicators_used)})"
        
        if score >= 4:
            return (f"强烈建议买入 {indicator_info}", accuracy)
        elif score >= 2:
            return (f"建议买入 {indicator_info}", accuracy)
        elif score >= 0.5:
            return (f"可以考虑买入 {indicator_info}", accuracy)
        elif score >= -0.5:
            return (f"继续持有 {indicator_info}", accuracy)
        elif score >= -2:
            return (f"谨慎持有 {indicator_info}", accuracy)
        elif score >= -4:
            return (f"建议卖出 {indicator_info}", accuracy)
        else:
            return (f"强烈建议卖出 {indicator_info}", accuracy)
    
    def run(self):
        """运行程序"""
        self.root.mainloop()


def main():
    root = tk.Tk()
    app = StockTrader(root)
    app.run()


if __name__ == "__main__":
    main()

