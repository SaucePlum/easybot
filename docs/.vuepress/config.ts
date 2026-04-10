import { viteBundler } from '@vuepress/bundler-vite'
import { plumeTheme } from 'vuepress-theme-plume'
import { defineUserConfig } from 'vuepress'

export default defineUserConfig({
  base: '/easybot/',
  lang: 'zh-CN',
  title: 'EasyBot SDK 帮助文档',
  description: 'QQ 官方机器人平台轻量级 Python SDK - 简洁、易上手、稳定',

  head: [
    ['meta', { name: 'theme-color', content: '#667eea' }],
    ['meta', { name: 'apple-mobile-web-app-capable', content: 'yes' }],
    ['meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black' }],
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/easybot/logo.svg' }],
    ['link', { rel: 'apple-touch-icon', href: '/easybot/logo.svg' }],
    ['meta', { name: 'keywords', content: 'EasyBot, QQ机器人, Python SDK, QQ开放平台, 机器人开发, Python' }],
    ['meta', { name: 'author', content: '小念同学' }],
    ['meta', { name: 'robots', content: 'index, follow' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'EasyBot SDK - QQ 官方机器人平台 Python SDK' }],
    ['meta', { property: 'og:description', content: 'QQ 官方机器人平台轻量级 Python SDK，简洁、易上手、稳定' }],
    ['meta', { property: 'og:image', content: '/easybot/logo.svg' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:title', content: 'EasyBot SDK - QQ 官方机器人平台 Python SDK' }],
    ['meta', { name: 'twitter:description', content: 'QQ 官方机器人平台轻量级 Python SDK，简洁、易上手、稳定' }],
  ],

  bundler: viteBundler({
    viteOptions: {
      server: {
        host: '0.0.0.0',
      },
    },
  }),

  theme: plumeTheme({
    logo: '/logo.svg',
    docsRepo: 'https://github.com/SaucePlum/easybot',
    docsDir: 'docs',
    docsBranch: 'main',
    lastUpdated: { formatOptions: { dateStyle: 'short', timeStyle: 'short' } },
    editLink: false,
    
    social: [
      { icon: 'github', link: 'https://github.com/SaucePlum/easybot' }
    ],

    navbar: [
      { text: '首页', link: '/', icon: 'mdi:home' },
      {
        text: '指南',
        icon: 'mdi:book',
        items: [
          { text: '简介', link: '/01_简介', icon: 'mdi:information' },
          { text: '快速入门', link: '/02_快速入门', icon: 'mdi:play' },
        ],
      },
      {
        text: '核心概念',
        icon: 'mdi:lightbulb',
        items: [
          { text: 'SDK组件', link: '/03_SDK组件', icon: 'mdi:puzzle' },
          { text: 'API参考', link: '/04_API参考', icon: 'mdi:api' },
          { text: 'Messages Model', link: '/05_Messages_Model', icon: 'mdi:message' },
          { text: 'Model库', link: '/06_Model库', icon: 'mdi:database' },
        ],
      },
      {
        text: '进阶',
        icon: 'mdi:rocket',
        items: [
          { text: '插件与权限', link: '/07_插件与权限', icon: 'mdi:key' },
          { text: 'Session会话管理器', link: '/08_Session会话管理器', icon: 'mdi:account' },
        ],
      },
      { text: '更新日志', link: '/11_更新日志', icon: 'mdi:history' },
      {
        text: '其他',
        icon: 'mdi:dots-horizontal',
        items: [
          { text: '常见问题', link: '/09_常见问题Q&A', icon: 'mdi:help-circle' },
          { text: '联系和反馈', link: '/10_联系和反馈', icon: 'mdi:email' },
        ],
      },
    ],

    sidebar: {
      '/': [
        {
          text: '开始',
          collapsed: false,
          items: [
            { text: '简介', link: '/01_简介' },
            { text: '快速入门', link: '/02_快速入门' },
          ],
        },
        {
          text: '核心概念',
          collapsed: false,
          items: [
            { text: 'SDK组件', link: '/03_SDK组件' },
            { text: 'API参考', link: '/04_API参考' },
            { text: 'Messages Model', link: '/05_Messages_Model' },
            { text: 'Model库', link: '/06_Model库' },
          ],
        },
        {
          text: '进阶',
          collapsed: false,
          items: [
            { text: '插件与权限', link: '/07_插件与权限' },
            { text: 'Session会话管理器', link: '/08_Session会话管理器' },
          ],
        },
        {
          text: '其他',
          collapsed: false,
          items: [
            { text: '常见问题', link: '/09_常见问题Q&A' },
            { text: '联系和反馈', link: '/10_联系和反馈' },
          ],
        },
      ],
    },
  }),
})
