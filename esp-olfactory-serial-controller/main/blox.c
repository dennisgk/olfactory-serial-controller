#include "blox.h"

blox_allocator blox_realloc(blox_allocator reset)
{
    static blox_allocator alloc = realloc;
    if (reset)
        alloc = reset;
    return alloc;
}

blox blox_nil(void)
{
    blox nil = {0};
    return nil;
}

blox blox_use_(const void *data, size_t length)
{
    blox buffer = {(void *)data, length, length};
    return buffer;
}

blox blox_make_(size_t width, size_t length, int reserved)
{
    blox buffer = {0};
    size_t size = length * width;
    if (reserved)
        blox_reserve(char, buffer, size);
    else
        blox_resize(char, buffer, size);
    buffer.length /= width;
    buffer.capacity /= width;
    return buffer;
}

blox blox_clone_(size_t width, const void *data, size_t length)
{
    size_t size = length * width;
    blox buffer = blox_make(char, size);
    memcpy(buffer.data, data, size);
    buffer.length = length;
    buffer.capacity /= width;
    return buffer;
}

blox blox_use_string_(size_t width, const void *data)
{
    typedef unsigned char byte;
    byte *base = ((byte *)data);
    byte *current = base;
    for (;;)
    {
        size_t count = width;
        do
        {
            if (*current != 0)
            {
                current += count;
                break;
            }
            else
                ++current;
        } while (--count);
        if (count == 0)
            break;
    }
    size_t length = ((current - base) / width) - 1;
    blox buffer = {base, length, length};
    return buffer;
}

void *blox_find_(void *key,
                 void *buffer,
                 size_t length,
                 size_t width,
                 blox_comparison comparison)
{
    typedef unsigned char byte;
    byte *current = (byte *)buffer;
    while (length--)
    {
        if (comparison(key, current) == 0)
            return current;
        current += width;
    }
    return NULL;
}

/*
 FIXME: Not entirely rigorous
*/
int blox_compare_(void *lhs, size_t lmx, void *rhs, size_t rmx, size_t width)
{
    if (lmx != rmx)
        return lmx < rmx ? -1 : 1;
    return memcmp(lhs, rhs, lmx * width);
}