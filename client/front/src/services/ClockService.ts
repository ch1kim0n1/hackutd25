/**
 * Clock Service
 * Manages market hours, calendar, and trading schedule
 */

import { AlpacaClient } from './AlpacaClient';
import type { Clock, Calendar } from './alpaca.types';

export class ClockService extends AlpacaClient {
  /**
   * Get current market clock
   */
  async getClock(): Promise<Clock> {
    try {
      const clock = await this.client.getClock();
      return clock as Clock;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Check if market is currently open
   */
  async isMarketOpen(): Promise<boolean> {
    try {
      const clock = await this.getClock();
      return clock.is_open;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get next market open time
   */
  async getNextOpen(): Promise<Date> {
    try {
      const clock = await this.getClock();
      return new Date(clock.next_open);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get next market close time
   */
  async getNextClose(): Promise<Date> {
    try {
      const clock = await this.getClock();
      return new Date(clock.next_close);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get market calendar
   */
  async getCalendar(params?: {
    start?: string | Date;
    end?: string | Date;
  }): Promise<Calendar[]> {
    try {
      const calendar = await this.client.getCalendar(params);
      return calendar as Calendar[];
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get today's trading hours
   */
  async getTodayHours(): Promise<Calendar | null> {
    try {
      const today = new Date();
      const todayStr = today.toISOString().split('T')[0];
      
      const calendar = await this.getCalendar({
        start: todayStr,
        end: todayStr,
      });

      return calendar.length > 0 ? calendar[0] : null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Get time until market opens/closes
   */
  async getTimeUntilMarketChange(): Promise<{
    isOpen: boolean;
    timeUntilChange: number; // milliseconds
    nextChangeTime: Date;
    nextChangeType: 'open' | 'close';
  }> {
    try {
      const clock = await this.getClock();
      const now = new Date(clock.timestamp);
      
      if (clock.is_open) {
        const nextClose = new Date(clock.next_close);
        return {
          isOpen: true,
          timeUntilChange: nextClose.getTime() - now.getTime(),
          nextChangeTime: nextClose,
          nextChangeType: 'close',
        };
      } else {
        const nextOpen = new Date(clock.next_open);
        return {
          isOpen: false,
          timeUntilChange: nextOpen.getTime() - now.getTime(),
          nextChangeTime: nextOpen,
          nextChangeType: 'open',
        };
      }
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get trading days in a date range
   */
  async getTradingDays(start: Date, end: Date): Promise<Calendar[]> {
    try {
      return await this.getCalendar({ start, end });
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Check if a specific date is a trading day
   */
  async isTradingDay(date: Date): Promise<boolean> {
    try {
      const dateStr = date.toISOString().split('T')[0];
      const calendar = await this.getCalendar({
        start: dateStr,
        end: dateStr,
      });
      return calendar.length > 0;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get next N trading days
   */
  async getNextTradingDays(count: number): Promise<Calendar[]> {
    try {
      const start = new Date();
      const end = new Date();
      end.setDate(end.getDate() + (count * 2)); // Get extra days to account for weekends/holidays

      const calendar = await this.getCalendar({ start, end });
      return calendar.slice(0, count);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get previous N trading days
   */
  async getPreviousTradingDays(count: number): Promise<Calendar[]> {
    try {
      const start = new Date();
      start.setDate(start.getDate() - (count * 2)); // Get extra days to account for weekends/holidays
      const end = new Date();

      const calendar = await this.getCalendar({ start, end });
      return calendar.slice(-count);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get market status with detailed information
   */
  async getMarketStatus(): Promise<{
    isOpen: boolean;
    currentTime: Date;
    nextOpen: Date;
    nextClose: Date;
    todayOpen?: string;
    todayClose?: string;
    timeUntilChange: number;
    timeUntilChangeFormatted: string;
  }> {
    try {
      const clock = await this.getClock();
      const todayHours = await this.getTodayHours();
      const timeInfo = await this.getTimeUntilMarketChange();

      const hours = Math.floor(timeInfo.timeUntilChange / (1000 * 60 * 60));
      const minutes = Math.floor((timeInfo.timeUntilChange % (1000 * 60 * 60)) / (1000 * 60));
      const timeUntilChangeFormatted = `${hours}h ${minutes}m`;

      return {
        isOpen: clock.is_open,
        currentTime: new Date(clock.timestamp),
        nextOpen: new Date(clock.next_open),
        nextClose: new Date(clock.next_close),
        todayOpen: todayHours?.open,
        todayClose: todayHours?.close,
        timeUntilChange: timeInfo.timeUntilChange,
        timeUntilChangeFormatted,
      };
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get market holidays in a year
   */
  async getMarketHolidays(year: number): Promise<Date[]> {
    try {
      const start = new Date(year, 0, 1);
      const end = new Date(year, 11, 31);
      
      const tradingDays = await this.getCalendar({ start, end });
      const tradingDates = new Set(tradingDays.map(day => day.date));
      
      const holidays: Date[] = [];
      const current = new Date(start);
      
      while (current <= end) {
        const dateStr = current.toISOString().split('T')[0];
        const dayOfWeek = current.getDay();
        
        // If it's a weekday but not a trading day, it's likely a holiday
        if (dayOfWeek !== 0 && dayOfWeek !== 6 && !tradingDates.has(dateStr)) {
          holidays.push(new Date(current));
        }
        
        current.setDate(current.getDate() + 1);
      }
      
      return holidays;
    } catch (error) {
      return this.handleError(error);
    }
  }
}

export default ClockService;
