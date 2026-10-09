import React from 'react';
import ReactDOM from 'react-dom/client';
import { App, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { BrowserRouter } from 'react-router-dom';
import InventoryApp from './app/App';
import './app/styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#0e7490', colorInfo: '#0e7490', colorText: '#172b3a', colorTextSecondary: '#526575', colorBgLayout: '#f4f7fa', colorBorderSecondary: '#e2e9ef', borderRadius: 10, fontFamily: "'Segoe UI', 'Microsoft YaHei', sans-serif", controlHeight: 40 } }}><App><BrowserRouter><InventoryApp /></BrowserRouter></App></ConfigProvider></React.StrictMode>,
);
