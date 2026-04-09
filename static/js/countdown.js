/**
 * Свадебный таймер обратного отсчёта
 * Дата свадьбы: 17 июля 2026 года, 16:00 (Ярославль)
 */

// Конфигурация таймера
const COUNTDOWN_CONFIG = {
    // Дата свадьбы: год, месяц (0-11), день, час, минута, секунда
    targetDate: new Date(2026, 6, 17, 16, 0, 0),
    // Элементы DOM для обновления
    elements: {
        weeks: 'weeks',
        days: 'days',
        hours: 'hours',
        minutes: 'minutes',
        seconds: 'seconds'
    },
    // Текст после завершения
    finishedMessage: {
        title: '❤️ Свадьба уже прошла! ❤️',
        subtitle: 'Но мы всегда рады видеть вас в гостях'
    }
};

// Класс для управления таймером (на случай, если понадобится несколько таймеров)
class CountdownTimer {
    constructor(config) {
        this.targetDate = config.targetDate.getTime();
        this.elements = config.elements;
        this.finishedMessage = config.finishedMessage;
        this.intervalId = null;
        this.isFinished = false;
    }

    // Форматирование числа с ведущим нулём
    static formatNumber(num) {
        return num.toString().padStart(2, '0');
    }

    // Получение DOM элемента с проверкой существования
    getElement(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Элемент с id "${id}" не найден`);
        }
        return element;
    }

    // Обновление значения элемента
    updateElement(id, value) {
        const element = this.getElement(id);
        if (element) {
            element.innerHTML = value;
        }
    }

    // Расчёт оставшегося времени
    calculateTimeLeft() {
        const now = new Date().getTime();
        const diff = this.targetDate - now;

        if (diff <= 0) {
            return null;
        }

        const weeks = Math.floor(diff / (1000 * 60 * 60 * 24 * 7));
        const days = Math.floor((diff % (1000 * 60 * 60 * 24 * 7)) / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);

        return { weeks, days, hours, minutes, seconds };
    }

    // Обновление отображения таймера
    updateDisplay() {
        const timeLeft = this.calculateTimeLeft();

        if (timeLeft === null) {
            this.showFinishedMessage();
            return;
        }

        this.updateElement(this.elements.weeks, timeLeft.weeks);
        this.updateElement(this.elements.days, CountdownTimer.formatNumber(timeLeft.days));
        this.updateElement(this.elements.hours, CountdownTimer.formatNumber(timeLeft.hours));
        this.updateElement(this.elements.minutes, CountdownTimer.formatNumber(timeLeft.minutes));
        this.updateElement(this.elements.seconds, CountdownTimer.formatNumber(timeLeft.seconds));
    }

    // Показ сообщения о завершении
    showFinishedMessage() {
        if (this.isFinished) return;
        this.isFinished = true;

        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }

        // Обновляем все значения на 0
        this.updateElement(this.elements.weeks, '0');
        this.updateElement(this.elements.days, '00');
        this.updateElement(this.elements.hours, '00');
        this.updateElement(this.elements.minutes, '00');
        this.updateElement(this.elements.seconds, '00');

        // Показываем сообщение (опционально)
        const countdownContainer = document.getElementById('countdown');
        if (countdownContainer && this.finishedMessage) {
            const finishedHtml = `
                <div class="countdown-finished" style="text-align: center; padding: 1rem;">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">${this.finishedMessage.title}</div>
                    <div style="font-size: 0.9rem; color: #666;">${this.finishedMessage.subtitle}</div>
                </div>
            `;
            // Можно раскомментировать, если нужно заменить таймер на сообщение
            // countdownContainer.innerHTML = finishedHtml;
        }

        console.log('Свадебный таймер завершил работу');
    }

    // Запуск таймера
    start() {
        // Первоначальное обновление
        this.updateDisplay();

        // Запуск интервала
        this.intervalId = setInterval(() => this.updateDisplay(), 1000);
    }

    // Остановка таймера
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}

// Создание и запуск таймера (только если DOM загружен)
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, существуют ли необходимые элементы
    const requiredElements = ['weeks', 'days', 'hours', 'minutes', 'seconds'];
    const allElementsExist = requiredElements.every(id => document.getElementById(id));
    
    if (!allElementsExist) {
        console.warn('Не все элементы таймера найдены на странице. Таймер не будет запущен.');
        return;
    }

    // Запускаем таймер
    const timer = new CountdownTimer(COUNTDOWN_CONFIG);
    timer.start();

    // Сохраняем таймер в глобальную переменную для отладки (опционально)
    if (typeof window !== 'undefined') {
        window.weddingTimer = timer;
    }
});

// Экспорт для модульного использования (если понадобится в будущем)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CountdownTimer, COUNTDOWN_CONFIG };
}