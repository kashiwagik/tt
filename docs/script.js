$(document).ready(function() {
    // --- アプリケーション状態管理クラス ---
    class TimetableState {
        constructor() {
            this.mode = 'day'; // 'day' or 'week'
            this.date = new Date();
            this.grade = null; // For week view
            this.target = 'undergrad'; // 'undergrad' or 'graduate'
            this.scheduleData = [];
            this.infoData = null;
            
            // 定数
            this.weekdays = ['日', '月', '火', '水', '木', '金', '土'];
            this.undergradGrades = ["1年生", "2年生", "3年生", "4年生", "4年助産"];
            this.graduateGrades = ["M1", "M2", "D1", "D2/3"];
            this.allGrades = this.undergradGrades.concat(this.graduateGrades);
            
            // 更新フラグ（無限ループ防止）
            this.isUpdating = false;
        }

        // URLパラメータから設定のみを読み込み（日付は除外）
        loadSettingsFromUrl() {
            const urlParams = new URLSearchParams(window.location.search);
            
            // 日付パラメータがある場合のみ読み込み（初回アクセス時など）
            if (urlParams.has('day')) {
                const dayParam = urlParams.get('day');
                const dateMatch = dayParam.match(/^(\d{4})[-]?(\d{2})[-]?(\d{2})$/);
                if (dateMatch) {
                    const year = parseInt(dateMatch[1]);
                    const month = parseInt(dateMatch[2]) - 1;
                    const day = parseInt(dateMatch[3]);
                    const newDate = new Date(year, month, day);
                    if (!isNaN(newDate.getTime())) {
                        this.date = newDate;
                    }
                }
            }
            
            // 表示モードパラメータの処理
            if (urlParams.has('type')) {
                const typeParam = urlParams.get('type').toLowerCase();
                if (typeParam === 'day' || typeParam === 'week') {
                    this.mode = typeParam;
                }
            }
            
            // 学年パラメータの処理（週表示用）
            if (urlParams.has('grade')) {
                const gradeParam = urlParams.get('grade');
                if (this.allGrades.includes(gradeParam)) {
                    this.grade = gradeParam;
                }
            }
            
            // 表示対象パラメータの処理（日表示用）
            if (urlParams.has('target')) {
                const targetParam = urlParams.get('target').toLowerCase();
                if (targetParam === 'undergrad' || targetParam === 'graduate') {
                    this.target = targetParam;
                }
            }
        }

        // 設定のみをURLに反映（日付は除外）
        syncSettingsToUrl() {
            if (this.isUpdating) return; // 更新中は処理しない
            
            const params = new URLSearchParams();
            
            if (this.mode === 'week' && this.grade) {
                params.set('type', 'week');
                params.set('grade', this.grade);
            } else {
                params.set('type', 'day');
                params.set('target', this.target);
            }
            
            const newUrl = `?${params.toString()}`;
            const currentUrl = window.location.search;
            
            // URLが変更された場合のみ更新
            if (newUrl !== currentUrl) {
                history.pushState(null, '', newUrl);
            }
        }

        // アクティブな学年リストを取得
        getActiveGrades() {
            return (this.target === 'graduate') ? this.graduateGrades : this.undergradGrades;
        }

        // 日付フォーマット
        formatDate(date, separator = '') {
            const year = date.getFullYear();
            const month = ('0' + (date.getMonth() + 1)).slice(-2);
            const day = ('0' + date.getDate()).slice(-2);
            return `${year}${separator}${month}${separator}${day}`;
        }

        // 週の月曜日を取得
        getMondayOfWeek(date) {
            const day = date.getDay();
            const diff = date.getDate() - day + (day === 0 ? -6 : 1);
            return new Date(date.setDate(diff));
        }
    }

    // --- ビュー管理クラス ---
    class TimetableView {
        constructor(state) {
            this.state = state;
        }

        // 全体のビューを更新（設定変更時のみURL同期）
        update(syncUrl = false) {
            this.state.isUpdating = true; // 更新フラグを設定
            
            this.updateModeSelector();
            this.updateDropdowns();
            this.updateDateDisplay();
            this.updateTimetable();
            
            this.state.isUpdating = false; // 更新フラグをクリア

            // 設定変更時のみURL同期
            if (syncUrl) {
                this.state.syncSettingsToUrl();
            }
            
        }

        // 日付のみ更新（URL同期なし）
        updateDateOnly() {
            this.updateDateDisplay();
            this.updateTimetable();
        }

        updateModeSelector() {
            $('.mode-option').removeClass('active');
            $(`.mode-option[data-mode="${this.state.mode}"]`).addClass('active');

            if (this.state.mode === 'day') {
                $('#week-dropdown').addClass('hidden');
                $('#day-dropdown').removeClass('hidden');
            } else {
                $('#week-dropdown').removeClass('hidden');
                $('#day-dropdown').addClass('hidden');
                
                // 週表示で学年が未選択の場合はデフォルトを設定
                if (!this.state.grade || !this.state.allGrades.includes(this.state.grade)) {
                    this.state.grade = this.state.allGrades[0];
                }
            }
        }

        updateDropdowns() {
            // 日表示用ドロップダウン
            $('#day-dropdown-toggle').text(this.state.target === 'undergrad' ? '学部' : '研究課程部');
            $('#day-dropdown-menu .dropdown-item').removeClass('active');
            $(`#day-dropdown-menu .dropdown-item[data-value="${this.state.target}"]`).addClass('active');

            // 週表示用ドロップダウン
            if (this.state.grade) {
                $('#week-dropdown-toggle').text(this.state.grade);
                $('#week-dropdown-menu .dropdown-item').removeClass('active');
                $(`#week-dropdown-menu .dropdown-item[data-value="${this.state.grade}"]`).addClass('active');
            }
        }

        updateDateDisplay() {
            if (this.state.mode === 'day') {
                const dayOfWeek = this.state.weekdays[this.state.date.getDay()];
                $('#current-date').text(
                    `${this.state.date.getFullYear()}年${this.state.date.getMonth() + 1}月${this.state.date.getDate()}日（${dayOfWeek}）`
                );
            } else {
                const weekStart = this.state.getMondayOfWeek(new Date(this.state.date));
                const weekEnd = new Date(weekStart);
                weekEnd.setDate(weekStart.getDate() + 4);

                $('#current-date').text(
                    `${weekStart.getFullYear()}年${weekStart.getMonth() + 1}月${weekStart.getDate()}日～${weekEnd.getMonth() + 1}月${weekEnd.getDate()}日`
                );
            }
        }

        updateTimetable() {
            const $table = $('#timetable');
            const $thead = $table.find('thead');
            const $tbody = $table.find('tbody');
            $thead.empty();
            $tbody.empty();

            if (this.state.mode === 'day') {
                this.displayDaySchedule($thead, $tbody);
            } else {
                if (this.state.grade) {
                    this.displayWeekSchedule($thead, $tbody);
                } else {
                    $tbody.html('<tr><td colspan="6">学年を選択してください。</td></tr>');
                }
            }
        }

        displayDaySchedule($thead, $tbody) {
            const activeGrades = this.state.getActiveGrades();
            
            // ヘッダー行の構築（リンクは設定変更のみ）
            let headerHtml = '<tr><th class="time-col">時限</th>';
            activeGrades.forEach(grade => {
                headerHtml += `<th><a href="?type=week&grade=${grade}">${grade}</a></th>`;
            });
            headerHtml += '</tr>';
            $thead.html(headerHtml);

            // ボディ行の構築
            const dateStr = this.state.formatDate(this.state.date, '-');
            for (let period = 1; period <= 5; period++) {
                let rowHtml = `<tr><td class="time-col">${period}限</td>`;
                activeGrades.forEach(grade => {
                    const entry = this.state.scheduleData.find(e => 
                        e.date === dateStr && e.grade === grade && e.period === period
                    );
                    if (entry && entry.courses) {
                        rowHtml += `<td class="class-td"><div class="class-cell"><div class="class-name">${entry.courses}</div><div class="class-room">${entry.room || ''}</div></div></td>`;
                    } else {
                        rowHtml += '<td class="empty-td">&nbsp;</td>';
                    }
                });
                rowHtml += '</tr>';
                $tbody.append(rowHtml);
            }
        }

        displayWeekSchedule($thead, $tbody) {
            const monday = this.state.getMondayOfWeek(new Date(this.state.date));
            const dates = [];
            const dateObjs = [];
            
            for (let i = 0; i < 5; i++) {
                const date = new Date(monday);
                date.setDate(monday.getDate() + i);
                dates.push(this.state.formatDate(date, '-'));
                dateObjs.push(date);
            }

            // ヘッダー行の構築（リンクは設定変更のみ）
            let headerHtml = '<tr><th class="time-col">時限</th>';
            dateObjs.forEach(dateObj => {
                const weekday = this.state.weekdays[dateObj.getDay()];
                headerHtml += `<th><a href="?type=day&target=${this.state.target}"><span class="date-header">${dateObj.getMonth() + 1}月${dateObj.getDate()}日<br/>${weekday}</span></a></th>`;
            });
            headerHtml += '</tr>';
            $thead.html(headerHtml);

            // ボディ行の構築
            for (let period = 1; period <= 5; period++) {
                let rowHtml = `<tr><td class="time-col">${period}限</td>`;
                dates.forEach(dateStr => {
                    const entry = this.state.scheduleData.find(e => 
                        e.date === dateStr && e.grade === this.state.grade && e.period === period
                    );
                    if (entry && entry.courses) {
                        rowHtml += `<td class="class-td"><div class="class-cell"><div class="class-name">${entry.courses}</div><div class="class-room">${entry.room || ''}</div></div></td>`;
                    } else {
                        rowHtml += '<td class="empty-td">&nbsp;</td>';
                    }
                });
                rowHtml += '</tr>';
                $tbody.append(rowHtml);
            }
        }
    }

    // --- イベントハンドラークラス ---
    class TimetableController {
        constructor(state, view) {
            this.state = state;
            this.view = view;
        }

        setupEventListeners() {
            // 日付ナビゲーション（URL更新なし）
            $('#prev-date').on('click', () => this.navigateDate(-1));
            $('#next-date').on('click', () => this.navigateDate(1));

            // モード切替（URL更新あり）
            $('.mode-option').on('click', (e) => {
                const mode = $(e.target).data('mode');
                this.switchMode(mode);
            });

            // ドロップダウン表示切替
            $('.dropdown-toggle').on('click', function() {
                const menu = $(this).next('.dropdown-menu');
                $('.dropdown-menu').not(menu).removeClass('show');
                menu.toggleClass('show');
            });

            // 週表示用学年選択（URL更新あり）
            $('#week-dropdown-menu .dropdown-item').on('click', (e) => {
                this.state.grade = $(e.target).data('value');
                $('.dropdown-menu').removeClass('show');
                this.view.update(true); // URL同期あり
            });

            // 日表示用対象選択（URL更新あり）
            $('#day-dropdown-menu .dropdown-item').on('click', (e) => {
                this.state.target = $(e.target).data('value');
                $('.dropdown-menu').removeClass('show');
                this.view.update(true); // URL同期あり
            });

            // ドロップダウン外クリックで閉じる
            $(document).on('click', function(e) {
                if (!$(e.target).closest('.custom-dropdown').length) {
                    $('.dropdown-menu').removeClass('show');
                }
            });
        }

        // 日付ナビゲーション（URL更新なし）
        navigateDate(direction) {
            const increment = this.state.mode === 'day' ? 1 : 7;
            this.state.date.setDate(this.state.date.getDate() + (direction * increment));
            this.view.updateDateOnly(); // 日付のみ更新、URL同期なし
        }

        // モード切替（URL更新あり）
        switchMode(mode) {
            if (this.state.mode === mode) return;
            
            this.state.mode = mode;
            if (mode === 'week' && (!this.state.grade || !this.state.allGrades.includes(this.state.grade))) {
                this.state.grade = this.state.allGrades[0];
            }
            this.view.update(true); // URL同期あり
        }
    }

    // --- データ管理クラス ---
    class TimetableDataManager {
        constructor(state) {
            this.state = state;
        }

        async loadScheduleData() {
            try {
                const data = await $.getJSON('schedule.json');
                this.state.scheduleData = data;
                console.log("Schedule data loaded successfully.");
            } catch (error) {
                console.error("Failed to load schedule.json:", error);
                this.state.scheduleData = [];
                throw new Error("Failed to load schedule data");
            }
        }

        async loadInfoData() {
            try {
                const infoData = await $.getJSON('info.json');
                this.state.infoData = infoData;
                if (infoData && infoData.last_modified) {
                    $('#last-modified').text('最終更新: ' + infoData.last_modified);
                } else {
                    $('#last-modified').text('最終更新: 不明');
                }
            } catch (error) {
                $('#last-modified').text('最終更新: 取得失敗');
            }
        }
    }

    // --- アプリケーション初期化 ---
    async function initializeApp() {
        const state = new TimetableState();
        const view = new TimetableView(state);
        const controller = new TimetableController(state, view);
        const dataManager = new TimetableDataManager(state);

        try {
            // URLパラメータから設定を読み込み（日付は初回のみ）
            state.loadSettingsFromUrl();
            
            // データを読み込み
            await dataManager.loadScheduleData();
            await dataManager.loadInfoData();
            
            // イベントリスナーを設定
            controller.setupEventListeners();
            
            // 初期表示を更新（URL同期あり）
            view.update(true);
            
        } catch (error) {
            console.error("Error initializing app:", error);
            $('#timetable > tbody').html('<tr><td colspan="6">時間割データの読み込みに失敗しました。</td></tr>');
            $('#current-date').text('エラー');
        }
    }

    // アプリケーション開始
    initializeApp();
});
