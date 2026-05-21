import { app, BrowserWindow, Menu, shell, dialog } from 'electron';
import { createServer as createNetServer } from 'node:net';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const appRoot = join(__dirname, '..');

let mainWindow = null;
let apiServer = null;
let apiPort = null;

function resolveSidecarPath() {
  const exe = process.platform === 'win32' ? 'github-radar-cli.exe' : 'github-radar-cli';
  const candidates = [
    join(process.resourcesPath || '', 'sidecar', process.platform === 'win32' ? 'win' : 'linux', exe),
    join(appRoot, 'dist-sidecar', process.platform === 'win32' ? 'win' : 'linux', exe),
  ];
  return candidates.find((p) => p && existsSync(p)) || '';
}

function findFreePort() {
  return new Promise((resolve, reject) => {
    const srv = createNetServer();
    srv.listen(0, '127.0.0.1', () => {
      const address = srv.address();
      const port = typeof address === 'object' && address ? address.port : 4420;
      srv.close(() => resolve(port));
    });
    srv.on('error', reject);
  });
}

function configureRuntimeEnv(port) {
  const userData = app.getPath('userData');
  const artifactsDir = join(userData, 'artifacts');
  const vaultDir = join(userData, 'vaults', 'AI-Vault');

  process.env.PORT = String(port);
  process.env.HOST = '127.0.0.1';
  process.env.GITHUB_RADAR_DATA_DIR = userData;
  process.env.ARTIFACTS_DIR = artifactsDir;
  process.env.OBSIDIAN_VAULT_PATH = vaultDir;
  const sidecarPath = resolveSidecarPath();
  if (sidecarPath) process.env.GITHUB_RADAR_SIDECAR_PATH = sidecarPath;

  return { userData, artifactsDir, vaultDir, sidecarPath };
}

async function startApiServer() {
  apiPort = await findFreePort();
  const paths = configureRuntimeEnv(apiPort);
  const { startServer } = await import('../server.mjs');
  apiServer = await startServer({ port: apiPort, host: '127.0.0.1' });
  return paths;
}

function buildMenu(paths) {
  const template = [
    {
      label: 'GitHub Radar',
      submenu: [
        {
          label: '打开数据目录',
          click: () => shell.openPath(paths.userData),
        },
        {
          label: '显示运行时信息',
          click: async () => dialog.showMessageBox({
            type: 'info',
            title: 'GitHub Radar Runtime',
            message: '运行时信息',
            detail: [
              `Data: ${paths.userData}`,
              `Artifacts: ${paths.artifactsDir}`,
              `Vault: ${paths.vaultDir}`,
              `Sidecar: ${paths.sidecarPath || 'not found yet'}`,
              `API: http://127.0.0.1:${apiPort}`,
            ].join('\n'),
          }),
        },
        {
          label: '打开界面',
          click: () => mainWindow?.loadURL(`http://127.0.0.1:${apiPort}`),
        },
        { type: 'separator' },
        { role: 'quit', label: '退出' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload', label: '重新加载' },
        { role: 'toggleDevTools', label: '开发者工具' },
        { type: 'separator' },
        { role: 'resetZoom', label: '重置缩放' },
        { role: 'zoomIn', label: '放大' },
        { role: 'zoomOut', label: '缩小' },
        { role: 'togglefullscreen', label: '全屏' },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

async function createWindow() {
  const paths = await startApiServer();
  buildMenu(paths);

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 980,
    minHeight: 640,
    title: 'GitHub Radar',
    backgroundColor: '#0f172a',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  try {
    await mainWindow.loadURL(`http://127.0.0.1:${apiPort}`);
  } catch (error) {
    await dialog.showMessageBox({
      type: 'error',
      title: 'GitHub Radar 启动失败',
      message: '无法加载 GitHub Radar UI。',
      detail: String(error?.stack || error),
    });
  }
}

app.whenReady().then(createWindow).catch(async (error) => {
  await dialog.showMessageBox({
    type: 'error',
    title: 'GitHub Radar 启动失败',
    message: 'Electron 初始化失败。',
    detail: String(error?.stack || error),
  });
  app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on('before-quit', () => {
  if (apiServer) {
    apiServer.close();
    apiServer = null;
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
