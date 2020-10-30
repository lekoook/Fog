#ifndef CIRCULAR_BUFFER_H_
#define CIRCULAR_BUFFER_H_

#include <stdlib.h>

/**
 * @brief Represents a circular buffer container containing object T. The capacity of this container is specified by N.
 * 
 * @tparam T Type of object to contain.
 * @tparam N Maximum number of objects to contain.
 */
template<typename T, size_t N>
class CircularBuffer
{
public:
    /**
     * @brief Constructs a new CircularBuffer object. This buffer implements a circular buffer mechanism.
     * When a new CircularBuffer is constructed with size N, the buffer can contain up to N number of
     * T objects. If a new values is inserted when the buffer is full, the oldest value inserted
     * will be replaced this this new T object.
     * 
     */
    CircularBuffer() :
        buf_(N ? new T[N] : nullptr),
        head_(0),
        tail_(0),
        max_size_(N),
        full_(false)
    {
    }

    /**
     * @brief Copy constructor for CircularBuffer objects.
     * 
     * @param value Rvalue to copy from.
     */
    CircularBuffer(const T& value) :
        buf_(N ? new T[N] : nullptr),
        head_(value.head_),
        tail_(value.tail_),
        max_size_(value.max_size_),
        full_(value.full_)
    {
        for (int i = 0; i < max_size_; i++)
        {
            buf_[i] = value.buf_[i];
        }
    }

    /**
     * @brief Destroys the CircularBuffer object.
     * 
     */
    ~CircularBuffer(void)
    {
        delete[] buf_;
    }

    /**
     * @brief Overloads the copy assignment operator.
     * 
     * @param other Rvalue to copy from.
     * @return CircularBuffer& Reference to the lvalue.
     */
    CircularBuffer& operator=(CircularBuffer other)
    {
        swap(*this, other);
        return *this;
    }

    /**
     * @brief Puts the value into the circular buffer as the newest T object.
     * 
     * @param value Object of T type.
     */
    void put(T value)
    {
        buf_[head_] = value; // Place or overwrite with the new IMUValue.
        if (full_)
        {
            // Since it was to begin with, increase the tail pointer.
            tail_ = (tail_ + 1) % max_size_;
        }
        head_ = (head_ + 1) % max_size_; // Always increase head pointer.
        full_ = head_ == tail_; // Update the full_ flag.
    }

    /**
     * @brief Retrieves the oldest value from the circular buffer.
     * @details This method will return a default empty value if the buffer is empty. To ensure you get valid values, always first check if the buffer is empty.
     * 
     * @return The oldest value in the buffer.
     */
    T get(void)
    {
        if (empty())
        {
            return T();
        }

        T ret = buf_[tail_];
        tail_ = (tail_ + 1) % max_size_;
        full_ = false;

        return ret;
    }

    /**
     * @brief Looks at the oldest from the circular buffer without removing it.
     * @details This method will return a default empty value if the buffer is empty. To ensure you get valid values, always first check if the buffer is empty.
     * 
     * @return The oldest value in the buffer.
     */
    T peek(void)
    {
        if (empty())
        {
            return T();
        }

        return buf_[tail_];
    }

    /**
     * @brief Looks at n-th item starting from the oldest item from the circular buffer without removing it.
     * 
     * @param n Index of n-th item starting from the oldest item. If zero is given, the oldest item is returned. To ensure you get valid values, you need to ensure n is lesser than the current number of items and always check if the buffer is empty.
     * @return T The n-th item starting from the oldest item.
     */
    T peek(uint8_t n)
    {
        if (empty() || n >= size())
        {
            return T();
        }

        return buf_[(tail_ + n) % max_size_];
    }

    /**
     * @brief Resets the circular buffer to empty buffer.
     * 
     */
    void reset(void)
    {
        head_ = tail_;
        full_ = false;
    }

    /**
     * @brief Check if circular buffer is empty.
     * 
     * @return true if empty.
     * @return false if not empty.
     */
    bool empty(void) const
    {
        return (!full_ && (head_ ==  tail_));
    }

    /**
     * @brief Check if circular buffer is full.
     * 
     * @return true if full.
     * @return false if empty.
     */
    bool full(void) const
    {
        return full_;
    }

    /**
     * @brief Returns the maximum size of circular buffer.
     * 
     * @return size_t maximum size of circular buffer.
     */
    size_t capacity(void) const
    {
        return max_size_;
    }

    /**
     * @brief Returns the number of elements in circular buffer.
     * 
     * @return size_t number of elements in circular buffer.
     */
    size_t size(void) const
    {
        size_t size = max_size_;

        if (!full_)
        {
            if (head_ >= tail_)
            {
                size = head_ - tail_;
            }
            else
            {
                size = max_size_ + head_ - tail_;
            }
        }

        return size;
    }

    /**
     * @brief Returns an array of the elements starting from the oldest item.
     * 
     * @param retArr Array buffer to store the elements.
     */
    void getArray(T retArr[size()])
    {
        for (int i = 0; i < size(); i++)
        {
            retArr[i] = buf_[(tail_ + i) % max_size_];
        }
    }

private:
    T* buf_;
    size_t head_;
    size_t tail_;
    const size_t max_size_;
    bool full_;
    friend void swap(CircularBuffer& first, CircularBuffer& second)
    {
        T* t_buf_ = first.buf_;
        size_t t_head_ = first.head_;
        size_t t_tail_ = first.tail_;
        bool t_full_ = first.full_;

        first.buf_ = second.buf_;
        first.head_ = second.head_;
        first.tail_ = second.tail_;
        first.full_ = second.full_;

        second.buf_ = t_buf_;
        second.head_ = t_head_;
        second.tail_ = t_tail_;
        second.full_ = t_full_;
    }
};

#endif // CIRCULAR_BUFFER_H_