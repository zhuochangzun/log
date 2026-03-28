// 单词学习助手 - 核心逻辑

const STORAGE_KEY = 'word_learner_data';
const SETTINGS_KEY = 'word_learner_settings';

// 默认设置
const DEFAULT_SETTINGS = {
    newPerDay: 5,
    intervals: [1, 3, 7, 14, 30] // 艾宾浩斯遗忘曲线间隔（天）
};

// 应用状态
let state = {
    words: [],
    learning: [], // 学习中
    settings: { ...DEFAULT_SETTINGS }
};

// 初始化
function init() {
    loadData();
    loadSettings();
    initEventListeners();
    updateStats();
    initPage();
}

// 加载数据
function loadData() {
    const data = localStorage.getItem(STORAGE_KEY);
    if (data) {
        const parsed = JSON.parse(data);
        state.words = parsed.words || [];
        state.learning = parsed.learning || [];
    }
}

// 保存数据
function saveData() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
        words: state.words,
        learning: state.learning
    }));
}

// 加载设置
function loadSettings() {
    const settings = localStorage.getItem(SETTINGS_KEY);
    if (settings) {
        state.settings = { ...DEFAULT_SETTINGS, ...JSON.parse(settings) };
    }
    // 更新设置界面
    document.getElementById('settingNewPerDay').value = state.settings.newPerDay;
    const intervals = state.settings.intervals;
    document.getElementById('interval1').value = intervals[0];
    document.getElementById('interval2').value = intervals[1];
    document.getElementById('interval3').value = intervals[2];
    document.getElementById('interval4').value = intervals[3];
    document.getElementById('interval5').value = intervals[4];
}

// 保存设置
function saveSettings() {
    state.settings.newPerDay = parseInt(document.getElementById('settingNewPerDay').value) || 5;
    state.settings.intervals = [
        parseInt(document.getElementById('interval1').value) || 1,
        parseInt(document.getElementById('interval2').value) || 3,
        parseInt(document.getElementById('interval3').value) || 7,
        parseInt(document.getElementById('interval4').value) || 14,
        parseInt(document.getElementById('interval5').value) || 30
    ];
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings));
    alert('设置已保存');
}

// 事件监听
function initEventListeners() {
    // 导航切换
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchPage(btn.dataset.page));
    });

    // 显示释义
    document.getElementById('btnShowMeaning').addEventListener('click', showMeaning);

    // 复习按钮
    document.getElementById('btnRemembered').addEventListener('click', () => handleReview(true));
    document.getElementById('btnForgot').addEventListener('click', () => handleReview(false));

    // 词库操作
    document.getElementById('btnAddWord').addEventListener('click', () => openModal());
    document.getElementById('wordSearch').addEventListener('input', renderWordList);

    // 弹窗操作
    document.getElementById('btnCancelModal').addEventListener('click', closeModal);
    document.getElementById('btnSaveWord').addEventListener('click', saveWord);

    // 导入操作
    document.querySelectorAll('input[name="format"]').forEach(radio => {
        radio.addEventListener('change', updateFormatHelp);
    });
    document.getElementById('btnImport').addEventListener('click', importWords);
    document.getElementById('btnImportSample').addEventListener('click', importSample);

    // 设置操作
    document.getElementById('btnSaveSettings').addEventListener('click', saveSettings);
    document.getElementById('btnResetData').addEventListener('click', resetData);
}

// 页面初始化
function initPage() {
    // 根据当前日期检查复习任务
    checkReviewTasks();
    // 更新统计
    updateStats();
    // 加载词库列表
    renderWordList();
}

// 页面切换
function switchPage(pageName) {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.page === pageName);
    });
    document.querySelectorAll('.page').forEach(page => {
        page.classList.toggle('active', page.id === `page-${pageName}`);
    });

    if (pageName === 'study') {
        loadStudyCard();
    } else if (pageName === 'library') {
        renderWordList();
    }
}

// ========== 学习相关 ==========

// 检查今日复习任务
function checkReviewTasks() {
    const today = getTodayStart();
    state.learning = state.learning.filter(item => {
        if (item.nextReview && new Date(item.nextReview) <= today) {
            return true;
        }
        // 已掌握的不需要复习
        if (item.level >= 5) return false;
        return true;
    });
    saveData();
}

// 获取今日开始时间
function getTodayStart() {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

// 获取今日新学的单词数
function getTodayNewCount() {
    const today = getTodayStart().getTime();
    return state.learning.filter(item => item.firstLearn && item.firstLearn >= today).length;
}

// 获取今日待复习的单词
function getTodayReviewWords() {
    const today = getTodayStart();
    return state.learning.filter(item => {
        if (!item.nextReview) return false;
        return new Date(item.nextReview) <= today;
    });
}

// 加载学习卡片
function loadStudyCard() {
    const reviewWords = getTodayReviewWords();
    const todayNewCount = getTodayNewCount();
    const maxNew = state.settings.newPerDay;

    const studyCard = document.getElementById('studyCard');
    const studyEmpty = document.getElementById('studyEmpty');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    // 优先复习，其次学习新词
    let currentWord = null;
    let isReview = false;

    if (reviewWords.length > 0) {
        currentWord = reviewWords[0];
        isReview = true;
    } else if (todayNewCount < maxNew) {
        // 还有新词名额，学习新词
        const newWords = state.words.filter(w => !state.learning.find(l => l.wordId === w.id));
        if (newWords.length > 0) {
            currentWord = {
                ...newWords[0],
                isNew: true,
                firstLearn: Date.now()
            };
            isReview = false;
        }
    }

    if (!currentWord) {
        studyCard.style.display = 'none';
        studyEmpty.classList.add('show');
        progressFill.style.width = '100%';
        progressText.textContent = '已完成';
        return;
    }

    studyCard.style.display = 'block';
    studyEmpty.classList.remove('show');

    // 显示单词
    document.getElementById('currentWord').textContent = currentWord.word;
    document.getElementById('reviewWord').textContent = currentWord.word;
    document.getElementById('currentPhonetic').textContent = currentWord.phonetic || '';
    document.getElementById('reviewPhonetic').textContent = currentWord.phonetic || '';
    document.getElementById('currentMeaning').textContent = currentWord.meaning;
    document.getElementById('currentExample').textContent = currentWord.example || '';

    // 重置卡片状态
    document.querySelector('.card-front').classList.add('show');
    document.querySelector('.card-back').classList.remove('show');
    document.getElementById('btnShowMeaning').style.display = 'block';

    // 更新进度
    const total = reviewWords.length + (maxNew - todayNewCount);
    const completed = 0; // 简化处理
    progressFill.style.width = `${(completed / Math.max(total, 1)) * 100}%`;
    progressText.textContent = `${completed} / ${total}`;

    // 保存当前学习的单词
    state.currentWord = currentWord;
    state.isReview = isReview;
}

// 显示释义
function showMeaning() {
    document.querySelector('.card-front').classList.remove('show');
    document.querySelector('.card-back').classList.add('show');
    document.getElementById('btnShowMeaning').style.display = 'none';
}

// 处理复习结果
function handleReview(remembered) {
    const current = state.currentWord;
    if (!current) return;

    if (current.isNew) {
        // 新词学习
        const learningItem = {
            wordId: current.id,
            word: current.word,
            meaning: current.meaning,
            phonetic: current.phonetic,
            example: current.example,
            level: remembered ? 1 : 0,
            nextReview: remembered ? getNextReviewTime(1) : getTodayStart().getTime(),
            firstLearn: current.firstLearn,
            lastReview: Date.now()
        };
        state.learning.push(learningItem);
    } else {
        // 复习旧词
        const item = state.learning.find(l => l.wordId === current.wordId);
        if (item) {
            if (remembered) {
                item.level = Math.min(item.level + 1, 5);
                item.nextReview = getNextReviewTime(item.level);
            } else {
                item.level = 0;
                item.nextReview = getTodayStart().getTime(); // 明天继续
            }
            item.lastReview = Date.now();
        }
    }

    saveData();
    updateStats();

    // 加载下一个
    setTimeout(loadStudyCard, 300);
}

// 计算下次复习时间
function getNextReviewTime(level) {
    const intervals = state.settings.intervals;
    const days = intervals[Math.min(level - 1, intervals.length - 1)] || 1;
    const next = new Date();
    next.setDate(next.getDate() + days);
    return next.getTime();
}

// ========== 词库相关 ==========

// 渲染词库列表
function renderWordList() {
    const search = document.getElementById('wordSearch').value.toLowerCase();
    const container = document.getElementById('wordList');

    // 合并词库和学习记录
    const allWords = state.words.map(w => {
        const learningItem = state.learning.find(l => l.wordId === w.id);
        return { ...w, learning: learningItem };
    }).filter(w => !search || w.word.toLowerCase().includes(search));

    if (allWords.length === 0) {
        container.innerHTML = '<div class="word-item"><div class="word-info"><p>暂无单词，请先导入或添加</p></div></div>';
        return;
    }

    container.innerHTML = allWords.map(w => {
        let statusClass = 'status-new';
        let statusText = '新词';
        if (w.learning) {
            if (w.learning.level >= 5) {
                statusClass = 'status-mastered';
                statusText = '已掌握';
            } else if (w.learning.level > 0) {
                statusClass = 'status-learning';
                statusText = `学习中 L${w.learning.level}`;
            }
        }

        return `
            <div class="word-item">
                <div class="word-info">
                    <div class="word">${w.word} <span class="word-status ${statusClass}">${statusText}</span></div>
                    <div class="details">
                        <span class="meaning-text">${w.meaning}</span>
                        ${w.phonetic ? ` · ${w.phonetic}` : ''}
                    </div>
                </div>
                <div class="word-actions">
                    <button class="btn-icon btn-edit" onclick="editWord(${w.id})">编辑</button>
                    <button class="btn-icon btn-delete" onclick="deleteWord(${w.id})">删除</button>
                </div>
            </div>
        `;
    }).join('');
}

// 打开弹窗
function openModal(wordId = null) {
    const modal = document.getElementById('wordModal');
    const title = document.getElementById('modalTitle');

    if (wordId) {
        const word = state.words.find(w => w.id === wordId);
        title.textContent = '编辑单词';
        document.getElementById('inputWord').value = word.word;
        document.getElementById('inputMeaning').value = word.meaning;
        document.getElementById('inputPhonetic').value = word.phonetic || '';
        document.getElementById('inputExample').value = word.example || '';
        state.editingWordId = wordId;
    } else {
        title.textContent = '添加单词';
        document.getElementById('inputWord').value = '';
        document.getElementById('inputMeaning').value = '';
        document.getElementById('inputPhonetic').value = '';
        document.getElementById('inputExample').value = '';
        state.editingWordId = null;
    }

    modal.classList.add('show');
}

// 关闭弹窗
function closeModal() {
    document.getElementById('wordModal').classList.remove('show');
}

// 保存单词
function saveWord() {
    const word = document.getElementById('inputWord').value.trim();
    const meaning = document.getElementById('inputMeaning').value.trim();
    const phonetic = document.getElementById('inputPhonetic').value.trim();
    const example = document.getElementById('inputExample').value.trim();

    if (!word || !meaning) {
        alert('单词和释义不能为空');
        return;
    }

    if (state.editingWordId) {
        // 编辑
        const idx = state.words.findIndex(w => w.id === state.editingWordId);
        if (idx !== -1) {
            state.words[idx] = { ...state.words[idx], word, meaning, phonetic, example };
        }
    } else {
        // 新增
        state.words.push({
            id: Date.now(),
            word,
            meaning,
            phonetic,
            example
        });
    }

    saveData();
    closeModal();
    renderWordList();
    updateStats();
}

// 编辑单词
function editWord(id) {
    openModal(id);
}

// 删除单词
function deleteWord(id) {
    if (!confirm('确定要删除这个单词吗？')) return;

    state.words = state.words.filter(w => w.id !== id);
    state.learning = state.learning.filter(l => l.wordId !== id);
    saveData();
    renderWordList();
    updateStats();
}

// ========== 导入相关 ==========

// 更新格式说明
function updateFormatHelp() {
    const format = document.querySelector('input[name="format"]:checked').value;
    const container = document.getElementById('formatExample');

    if (format === 'json') {
        container.innerHTML = `<pre>{
  "words": [
    {"word": "hello", "meaning": "你好", "phonetic": "/həˈloʊ/", "example": "Hello, world!"},
    {"word": "computer", "meaning": "电脑", "phonetic": "/kəmˈpjuːtər/", "example": "I use a computer."}
  ]
}</pre>`;
    } else {
        container.innerHTML = `<pre>word,meaning,phonetic,example
hello,你好,/həˈloʊ/,Hello world!
computer,电脑,/kəmˈpjuːtər/,I use a computer.</pre>`;
    }
}

// 导入词库
function importWords() {
    const format = document.querySelector('input[name="format"]:checked').value;
    const text = document.getElementById('importText').value.trim();

    if (!text) {
        alert('请输入词库内容');
        return;
    }

    try {
        let words = [];

        if (format === 'json') {
            const data = JSON.parse(text);
            words = Array.isArray(data) ? data : (data.words || []);
        } else {
            // CSV 解析
            const lines = text.split('\n').filter(l => l.trim());
            const headers = lines[0].toLowerCase().split(',').map(h => h.trim());

            for (let i = 1; i < lines.length; i++) {
                const values = lines[i].split(',').map(v => v.trim());
                const word = {};
                headers.forEach((h, idx) => {
                    if (h === 'word') word.word = values[idx];
                    if (h === 'meaning') word.meaning = values[idx];
                    if (h === 'phonetic') word.phonetic = values[idx];
                    if (h === 'example') word.example = values[idx];
                });
                if (word.word && word.meaning) {
                    words.push(word);
                }
            }
        }

        // 去重
        const existingWords = new Set(state.words.map(w => w.word.toLowerCase()));
        const newWords = words.filter(w => !existingWords.has(w.word.toLowerCase())).map(w => ({
            id: Date.now() + Math.random(),
            word: w.word,
            meaning: w.meaning,
            phonetic: w.phonetic || '',
            example: w.example || ''
        }));

        state.words.push(...newWords);
        saveData();
        updateStats();

        alert(`成功导入 ${newWords.length} 个单词`);
        document.getElementById('importText').value = '';
    } catch (e) {
        alert('导入失败，请检查格式是否正确\n' + e.message);
    }
}

// 导入示例
function importSample() {
    const sample = {
        words: [
            { word: 'hello', meaning: '你好', phonetic: '/həˈloʊ/', example: 'Hello, world!' },
            { word: 'computer', meaning: '电脑', phonetic: '/kəmˈpjuːtər/', example: 'I use a computer every day.' },
            { word: 'programming', meaning: '编程', phonetic: '/ˈproʊɡræmɪŋ/', example: 'Programming is fun.' },
            { word: 'algorithm', meaning: '算法', phonetic: '/ˈælɡərɪðəm/', example: 'The algorithm is efficient.' },
            { word: 'database', meaning: '数据库', phonetic: '/ˈdeɪtəbeɪs/', example: 'Store data in a database.' },
            { word: 'network', meaning: '网络', phonetic: '/ˈnetwɜːrk/', example: 'Connect to the network.' },
            { word: 'browser', meaning: '浏览器', phonetic: '/ˈbraʊzər/', example: 'Open a new browser.' },
            { word: 'keyboard', meaning: '键盘', phonetic: '/ˈkiːbɔːrd/', example: 'Type on the keyboard.' },
            { word: 'software', meaning: '软件', phonetic: '/ˈsɔftwer/', example: 'Install the software.' },
            { word: 'interface', meaning: '界面', phonetic: '/ˈɪntərfeɪs/', example: 'The interface is user-friendly.' }
        ]
    };

    document.getElementById('importText').value = JSON.stringify(sample, null, 2);
    document.querySelector('input[value="json"]').checked = true;
    updateFormatHelp();
}

// ========== 设置相关 ==========

// 重置数据
function resetData() {
    if (!confirm('确定要清除所有数据吗？此操作不可恢复！')) return;

    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(SETTINGS_KEY);
    state.words = [];
    state.learning = [];
    state.settings = { ...DEFAULT_SETTINGS };

    loadSettings();
    updateStats();
    renderWordList();

    alert('数据已重置');
}

// ========== 统计相关 ==========

// 更新统计
function updateStats() {
    const total = state.words.length;
    const mastered = state.learning.filter(l => l.level >= 5).length;
    const todayReview = getTodayReviewWords().length;
    const todayNew = getTodayNewCount();

    document.getElementById('totalWords').textContent = total;
    document.getElementById('masteredWords').textContent = mastered;
    document.getElementById('todayReview').textContent = todayReview;
    document.getElementById('todayNew').textContent = `${todayNew}/${state.settings.newPerDay}`;
}

// 启动应用
init();