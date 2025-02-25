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


function formatExecutionTime(seconds) {
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


async function checkTaskStatus(taskId) {
    try {
        const response = await fetch(`/unloading/status/${taskId}`);
        const data = await response.json();
        console.log(data);

        if (data.error) {
            console.error(data.data);
            return [null, null]; // Return nulls if there's an error
        } else {
            const { result, start_time, timestamp } = data.data;
            const executionTimeSec = (new Date(timestamp) - new Date(start_time)) / 1000;
            const executionTime = formatExecutionTime(executionTimeSec);
            return [result, executionTime];
        }
    } catch (error) {
        console.error('Ошибка при запросе статуса задачи:', error);
        return [null, null]; // Return nulls in case of an error
    }
}


async function checkAllTasks() {

    const taskElements = document.querySelectorAll('.taskprocess');
    const updates = [];

    const taskPromises = Array.from(taskElements).map(async (element) => {
        const taskId = element.getAttribute('data-task-id');
        const [result, executionTime] = await checkTaskStatus(taskId);
        return { element, result, executionTime };
    });

    const taskResults = await Promise.all(taskPromises);

    taskResults.forEach(({ element, result, executionTime }) => {
        const taskWorking = element.querySelector('.taskworking');
        const taskError = element.querySelector('.taskerror');
        const taskJson = element.querySelector('.taskjson');
        const taskCsv = element.querySelector('.taskcsv');
        const taskTotal = element.querySelector('.tasktotal');

        if (result) {

            if (taskError && result.error) {
                updates.push({ element: taskError, style: { display: '' }, title: result.data, href: `/unloading?error=${encodeURIComponent(result.data)}` });
            }

            if (!result.error) {
                if (taskJson) { updates.push({ element: taskJson, style: { display: '' } }); }
                if (taskCsv) { updates.push({ element: taskCsv, style: { display: '' } }); }
                if (taskTotal) {
                    updates.push({ element: taskTotal, textContent: result.data['total'], style: { display: '' } });
                }
            }

            element.classList.remove('taskprocess');

        } else if (executionTime) {

            if (taskWorking) {
                updates.push({ element: taskWorking, style: { display: '' }, textContent: executionTime });
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

    const url = `/search?mm=${mm}&t=${t}&q=${q}&p=${p}`;

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
        location.href = `${loc}?mm=${mm}&t=${t}&q=${q}&p=${p}`
    }
    else if (loc == '/unloading') {
        // nothing
        // location.href = `${loc}?t=${t}&q=${q}`
    }
}


function handlePageInputChange() {
    const t = encodeURIComponent(document.getElementById('tableInput')?.value || '');
    const q = encodeURIComponent(document.getElementById('queryInput')?.value || '');
    const mm = encodeURIComponent(document.getElementById('maxMatchesInput')?.value || 100);
    const p = encodeURIComponent(this.value);
    const loc = location.pathname;

    const url = `${loc}?mm=${mm}&t=${t}&q=${q}&p=${p}`;

    location.href = url;
}

async function startTaskUpdates() {
    while (true) {
        await checkAllTasks();
        await new Promise(resolve => setTimeout(resolve, 1000));
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

}

// Run the initialization function
init();