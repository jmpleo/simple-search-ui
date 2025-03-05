// Function to hide the loading spinner
function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

// Function to show the loading spinner
function showLoading() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'flex';
    }
}


function formatExecutionTime(ms) {
    if (ms < 1000) {
        return `${ms}ms`;
    }

    const seconds = ms / 1000;
    let formattedTime;

    if (seconds < 60) {
        formattedTime = `${seconds.toFixed(0)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = (seconds % 60).toFixed(0);
        formattedTime = `${minutes}m ${remainingSeconds}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = (seconds % 60).toFixed(0);
        formattedTime = `${hours}h ${minutes}m ${remainingSeconds}s`;
    }

    return formattedTime;
}

function reduceLargeNumber(num) {
    // Пробуем преобразовать num в число
    num = Number(num);

    // Проверяем на NaN и отрицательные числа
    if (isNaN(num) || num < 0) {
        return 'NaN';
    } else if (num < 1000) {
        return Math.round(num).toString();
    } else if (num < 1_000_000) {
        return (num / 1000).toFixed(1) + 'K';
    } else if (num < 1_000_000_000) {
        return (num / 1_000_000).toFixed(1) + 'M';
    } else if (num < 1_000_000_000_000) {
        return (num / 1_000_000_000).toFixed(3) + 'B';
    } else if (num < 1_000_000_000_000_000) {
        return (num / 1_000_000_000_000).toFixed(3) + 'T';
    } else if (num < 1_000_000_000_000_000_000) {
        return (num / 1_000_000_000_000_000).toFixed(3) + 'Qd';
    } else if (num < 1_000_000_000_000_000_000_000) {
        return (num / 1_000_000_000_000_000_000).toFixed(3) + 'Qn';
    } else {
        return 'NaN';
    }
}

function animationIncreaseValues() {
    const elements = document.querySelectorAll('.metric.value');
    if (elements) {
        elements.forEach(element => {
            const targetNumber = parseInt(element.getAttribute('data-value'), 10);
            let currentNumber = 0;
            const duration = 2000; // Длительность анимации в миллисекундах
            const incrementTime = 50; // Интервал времени для каждого увеличения в миллисекундах
            const totalSteps = duration / incrementTime; // Общее количество шагов
            const incrementValue = targetNumber / totalSteps; // Значение для увеличения на каждом шаге

            function animateCounter() {
                currentNumber += incrementValue;

                dataValue = Math.floor(currentNumber);
                element.setAttribute('data-value', dataValue);

                if (currentNumber < targetNumber) {
                    if (element.classList.contains('time')) {
                        element.textContent = formatExecutionTime(dataValue);
                    } else if (element.classList.contains('big-number')) {
                        element.textContent = reduceLargeNumber(dataValue);
                    } else {
                        element.textContent = dataValue;
                    }
                    requestAnimationFrame(animateCounter);
                } else {
                    if (element.classList.contains('time')) {
                        element.textContent = formatExecutionTime(targetNumber);
                    } else if (element.classList.contains('big-number')) {
                        element.textContent = reduceLargeNumber(targetNumber);
                    } else {
                        element.textContent = targetNumber;
                    }
                }
            }

            animateCounter();
        });
    }
}

async function checkTaskStatus(taskId) {
    try {
        const response = await fetch(`/unloading/status/${taskId}`);
        const data = await response.json();
        //console.log(data);
        if (data['error']) {
            return [true, null, null];
        } else if (data['data']) {
            const { result, start_time, timestamp } = data['data'];
            const executionTimeMs = (new Date(timestamp) - new Date(start_time));
            const executionTime = formatExecutionTime(executionTimeMs);
            return [false, result, executionTime];
        }
    } catch (error) {
        //console.error('Ошибка при запросе статуса задачи:', error);
        return [false, null, null];
    }
}


/*
async function checkAllTasks() {
    const taskElements = document.querySelectorAll('.task-in-progress, .task-completed');

    const t = encodeURIComponent(document.getElementById('tableInput')?.value || '');

    const updates = [];

    const taskPromises = Array.from(taskElements).map(async (element) => {
        const taskId = element.getAttribute('data-task-id');
        const [expired, result, executionTime] = await checkTaskStatus(taskId);
        return { element, expired, result, executionTime, taskId }; // Include taskId in the return object
    });

    const taskResults = await Promise.all(taskPromises);

    taskResults.forEach(({ element, expired, result, executionTime, taskId }) => {

        if (expired) {
            const tr = document.getElementById(taskId);
            if (tr) {
                tr.style.transition = "opacity 1s ease";
                tr.style.opacity = 0.5;
                // tr.addEventListener('transitionend', function() {
                //     tr.remove();
                // });
            }
            return;
        }

        if (element.classList.contains('.task-completed')) {
            return;
        }

        const taskProgress = element.querySelector('.task-progress');
        const taskError = element.querySelector('.task-error');
        const taskJson = element.querySelector('.task-json');
        const taskCsv = element.querySelector('.task-csv');
        const taskTotal = element.querySelector('.task-total');
        const ballRoller = element.querySelector('.ball-roller');

        if (result) {

            if (taskProgress) {
                updates.push({
                    element: taskProgress,
                    style: { display: 'none' }
                });
            }

            if (ballRoller) {
                updates.push({
                    element: ballRoller,
                    style: { display: 'none' }
                });
            }

            if (taskError && result.error) {
                updates.push({
                    element: taskError,
                    style: { display: '' },
                    title: `${result.data}`,
                    href: `/unloading?t=${t}&error=${encodeURIComponent(result.data)}`
                });
                const tr = document.getElementById(taskId);
            }

            if (!result.error) {

                if (taskTotal && result.data['total_pretty']) {
                    updates.push({
                        element: taskTotal,
                        textContent: result.data['total_pretty'] + " строк",
                        style: { display: '' }
                    });
                }

                if (taskJson && result.data['total'] > 0) {
                    updates.push({
                        element: taskJson,
                        style: { display: '' }
                    });
                }

                if (taskCsv && result.data['total']) {
                    updates.push({
                        element: taskCsv,
                        style: { display: '' }
                    });
                }
            }

            element.classList.remove('task-in-progress');
            element.classList.add('task-completed');

        } else if (executionTime) {

            if (taskProgress) {
                updates.push({
                    element: taskProgress,
                    style: { display: '' },
                    textContent: executionTime
                });
            }
        }
    });

    updates.forEach(update => {
        if (update.style) {
            Object.assign(update.element.style, update.style);
        }
        if (update.textContent !== undefined) {
            update.element.textContent = update.textContent;
        }
        if (update.href) {
            update.element.href = update.href;
        }
    });
}
*/

async function checkAllTasks() {
    const taskElements = document.querySelectorAll('.task-in-progress, .task-completed');
    const t = encodeURIComponent(document.getElementById('tableInput')?.value || '');
    const updates = [];
    const batchSize = 5;
    const delay = 100;

    const processBatch = async (startIndex) => {
        const endIndex = Math.min(startIndex + batchSize, taskElements.length);
        const taskPromises = Array.from(taskElements).slice(startIndex, endIndex).map(async (element) => {
            const taskId = element.getAttribute('data-task-id');
            const [expired, result, executionTime] = await checkTaskStatus(taskId);
            return { element, expired, result, executionTime, taskId };
        });

        const taskResults = await Promise.all(taskPromises);

        taskResults.forEach(({ element, expired, result, executionTime, taskId }) => {

            const tr = document.getElementById(taskId);
            const taskProgress = element.querySelector('.task-progress');
            const taskError = element.querySelector('.task-error');
            const taskJson = element.querySelector('.task-json');
            const taskCsv = element.querySelector('.task-csv');
            const taskZip = element.querySelector('.task-zip');
            const taskTotal = element.querySelector('.task-total');
            const ballRoller = element.querySelector('.ball-roller');

            if (expired) {
                if (taskError) {
                    updates.push({
                        element: taskError,
                        style: { display: '' },
                        textContent: 'протухло',
                        href: '#'
                    });
                }
                if (taskProgress) {
                    if (executionTime) {
                        updates.push({ element: taskProgress, style: {
                            display: '',
                            textContent: executionTime
                        } });
                    } else {
                        updates.push({ element: taskProgress, style: {
                            display: 'none'
                        } });
                    }
                }
                if (taskJson) {
                    updates.push({ element: taskJson, style: { display: 'none' } });
                }
                if (taskZip) {
                    updates.push({ element: taskZip, style: { display: 'none' } });
                }
                if (taskCsv) {
                    updates.push({ element: taskCsv, style: { display: 'none' } });
                }
                if (ballRoller) {
                    updates.push({ element: ballRoller, style: { display: 'none' } });
                }
                if (tr) {
                    tr.style.transition = "opacity 1s ease";
                    tr.style.opacity = 0.5;
                    element.classList.remove('task-completed');
                    element.classList.remove('task-in-progress');
                }

                return;
            }

            if (element.classList.contains('task-completed')) {
                return;
            }

            if (result) {
                if (taskProgress) {
                    if (executionTime) {
                        updates.push({ element: taskProgress, style: {
                            display: '',
                            textContent: executionTime
                        } });
                    } else {
                        updates.push({ element: taskProgress, style: {
                            display: 'none'
                        } });
                    }
                }
                if (ballRoller) {
                    updates.push({ element: ballRoller, style: { display: 'none' } });
                }
                if (taskError && result['error'] && result['data']) {
                    updates.push({
                        element: taskError,
                        style: { display: '' },
                        title: `${result['data']}`,
                        textContent: `ошибочка`,
                        href: `/unloading?t=${t}&error=${encodeURIComponent(result['data'])}`
                    });
                }

                if (!result['error'] && result['data']) {
                    if (taskTotal && result['data']['total_pretty']) {
                        updates.push({
                            element: taskTotal,
                            textContent: "строк: " + result['data']['total_pretty'],
                            style: { display: '' }
                        });
                    }
                    if (taskJson && result['data']['total'] > 0) {
                        updates.push({ element: taskJson, style: { display: '' } });
                    }
                    if (taskCsv && result['data']['total']) {
                        updates.push({ element: taskCsv, style: { display: '' } });
                    }
                    if (taskZip && result['data']['total']) {
                        updates.push({ element: taskZip, style: { display: '' } });
                    }
                }

                element.classList.remove('task-in-progress');
                element.classList.add('task-completed');

            } else if (executionTime) {
                if (taskProgress) {
                    updates.push({
                        element: taskProgress,
                        style: { display: '' },
                        textContent: executionTime
                    });
                }
            }

        });

        // Применяем обновления к DOM
        updates.forEach(update => {
            if (update.style) {
                Object.assign(update.element.style, update.style);
            }
            if (update.textContent !== undefined) {
                update.element.textContent = update.textContent;
            }
            if (update.href) {
                update.element.href = update.href;
            }
        });

        // Если есть еще задачи, обрабатываем следующий пакет
        if (endIndex < taskElements.length) {
            setTimeout(() => processBatch(endIndex), delay);
        }
    };

    // Начинаем обработку с первой партии
    await processBatch(0);
}


// Function to handle form submission
async function handleUnloadFormSubmit(event) {
    event.preventDefault();

    showLoading();

    const t = encodeURIComponent(document.getElementById('tableInput')?.value || '');
    const q = encodeURIComponent(document.getElementById('queryInput')?.value || '');

    const url = `/unloading/start?t=${t}&q=${q}`;

    try {
        const response = await fetch(url);

        if (response.redirected) {

            location.href = response.url
        }
        else {
            location.href = `/unloading?t=${t}`;
        }

    } catch (error) {
        console.error('Ошибка при запросе начала задачи:', error);
    }
}


function handleSearchFormSubmit(event) {

    showLoading();

    event.preventDefault();
    const t = encodeURIComponent(document.getElementById('tableInput')?.value || '');
    const q = encodeURIComponent(document.getElementById('queryInput')?.value || '');
    const mm = encodeURIComponent(document.getElementById('maxMatchesInput')?.value || 100);
    const p = encodeURIComponent(document.getElementById('pageInput')?.value || 0);

    const url = `/search?mm=${mm}&t=${t}&q=${q}`;

    location.href = url;
}


function handleRefreshClick() {

    showLoading();

    const t = encodeURIComponent(document.getElementById('tableInput')?.value || '');
    const url = `/unloading?t=${t}`;

}

// Function to handle input change and redirect
function handleTableInputChange() {
    const t = encodeURIComponent(this.value);
    const q = encodeURIComponent(document.getElementById('queryInput')?.value || '');
    const mm = encodeURIComponent(document.getElementById('maxMatchesInput')?.value || 100);
    const p = encodeURIComponent(document.getElementById('pageInput')?.value || 0);
    const loc = location.pathname;

    if (loc == '/search') {
        // location.href = `${loc}?mm=${mm}&t=${t}&q=${q}&p=${p}`
        // location.href = `${loc}?t=${t}`
    }
    else if (loc == '/unloading') {
        // nothing
        // location.href = `${loc}?t=${t}&q=${q}`
    }
}


function handlePageInputChange() {
    showLoading();
    const t = encodeURIComponent(document.getElementById('tableInput')?.value || '');
    const q = encodeURIComponent(document.getElementById('queryInput')?.value || '');
    const mm = encodeURIComponent(document.getElementById('maxMatchesInput')?.value || 100);
    const p = encodeURIComponent(this.value);
    const loc = location.pathname;

    const url = `${loc}?mm=${mm}&t=${t}&q=${q}&p=${p}`;

    location.href = url;
}

// Prevent default behavior for drag and drop events
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight the drop area
function highlight(dropArea) {
    dropArea.classList.add('hover');
}

// Remove highlight from the drop area
function unhighlight(dropArea) {
    dropArea.classList.remove('hover');
}

// Handle the drop event
function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

// Handle the files dropped or selected
function handleFiles(files) {
    Array.from(files).forEach(uploadFile);
}

// Upload a single file to the server
async function uploadFile(file) {

    showLoading();

    const t = encodeURIComponent(document.getElementById('tableInput')?.value || '');
    const url = `/unloading/start?t=${t}`;
    const formData = new FormData();

    formData.append('file', file);

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
        });

        body = response.json();

        if (body['error'] && body['data']) {
            location.href = `/unloading?t=${t}&error=${body['data']}`;
        } else {
            location.href = `/unloading?t=${t}`;
        }
    } catch (error) {
        console.error('Error during task initiation request:', error);
    }
}

// Initialize the drop area for drag and drop functionality
function initDropArea(dropArea) {
    const events = ['dragenter', 'dragover', 'dragleave', 'drop'];

    // Prevent default behavior for drag and drop events
    events.forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight the drop area when an item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => highlight(dropArea), false);
    });

    // Remove highlight when the item is no longer hovering
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => unhighlight(dropArea), false);
    });

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
}


async function startTaskUpdates() {
    while (true) {
        await checkAllTasks();
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
}


function startWrappedSeqs() {
    const tdElements = document.querySelectorAll('.rawtable td');
    tdElements.forEach(td => {
        td.innerHTML = td.innerHTML.replace(
            /(\d{2,})/g, "<span class='digits'>$1</span>");

        td.innerHTML = td.innerHTML.replace(
            /([\-@.#%^*()\[\]{},;:!?_]+)/g, "<span class='specs'>$1</span>");


    });
}


// Initialize event listeners
function init() {
    document.addEventListener('DOMContentLoaded', () => {
        checkAllTasks();
        startWrappedSeqs();
        hideLoading();
        animationIncreaseValues();
    });

    startTaskUpdates();

    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchFormSubmit);
    }

    const tableInput = document.getElementById('tableInput');
    if (tableInput) {
        tableInput.addEventListener('change', handleTableInputChange);
    }

    const pageInput = document.getElementById('pageInput');
    if (pageInput) {
        pageInput.addEventListener('change', handlePageInputChange);
    }

    const unloadForm = document.getElementById('unloadForm');
    if (unloadForm) {
        unloadForm.addEventListener('submit', handleUnloadFormSubmit);
    }

    const refreshButton = document.getElementById('refresh');
    if (refreshButton) {
        refreshButton.addEventListener('click', handleRefreshClick);
    }

    const dropArea = document.getElementById('draggable');
    if (dropArea) {
        initDropArea(dropArea);
    }

}

// Run the initialization function
init();