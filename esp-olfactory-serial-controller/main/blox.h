#ifndef BLOX_H
#define BLOX_H

/* Minimal, header-only blox — no external deps.
   Implements just what olfactory_{loop,serial}.c use.
*/
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/* Public type (unchanged) */
typedef struct blox
{
    void *data;      /* pointer to T */
    size_t length;   /* number of T elements */
    size_t capacity; /* number of T elements allocated */
} blox;

/* ---------- internal helpers (bytes-based growth) ---------- */

static inline void __blox_reserve_bytes(blox *v, size_t elem_size, size_t need_bytes)
{
    size_t need_elems = (need_bytes + elem_size - 1) / elem_size; /* round up */
    if (v->capacity >= need_elems)
        return;

    size_t newcap = v->capacity ? v->capacity : 2;
    while (newcap < need_elems)
    {
        size_t nxt = newcap << 1;
        if (nxt < newcap)
        { /* overflow guard */
            newcap = need_elems;
            break;
        }
        newcap = nxt;
    }

    void *p = realloc(v->data, newcap * elem_size);
    if (!p)
    {
        /* fallback: try exact */
        p = realloc(v->data, need_elems * elem_size);
        if (!p)
        {
            abort();
        }
        newcap = need_elems;
    }
    v->data = p;
    v->capacity = newcap;
}

static inline void __blox_resize_elems(blox *v, size_t elem_size, size_t new_len_elems)
{
    __blox_reserve_bytes(v, elem_size, new_len_elems * elem_size);
    v->length = new_len_elems;
}

/* ---------- constructors / basic utilities ---------- */

static inline blox blox_nil(void)
{
    blox b = (blox){0};
    return b;
}

/* Non-owning view (length is element-count) */
static inline blox blox_use_(const void *data, size_t length)
{
    blox b;
    b.data = (void *)data;
    b.length = length;
    b.capacity = length;
    return b;
}

/* Owning make: allocate for `length` elements; set length = capacity = length */
static inline blox blox_make_(size_t width, size_t length, int /*reserved*/)
{
    (void)0;
    blox b = {0};
    __blox_reserve_bytes(&b, width, length * width);
    b.length = length;
    b.capacity = (b.capacity < length) ? length : b.capacity; /* set by reserve */
    return b;
}

/* Clone raw memory (length in elements) */
static inline blox blox_clone_(size_t width, const void *data, size_t length)
{
    blox out = blox_make_(width, length, 0);
    if (length)
        memcpy(out.data, data, length * width);
    return out;
}

/* Map macro-call to the inline above */
#define blox_clone(T, other_b) \
    blox_clone_(sizeof(T), (other_b).data, (other_b).length)

/* Free (only use on owning buffers — your callsites do) */
#define blox_free(v)                   \
    do                                 \
    {                                  \
        if ((v).data)                  \
            free((v).data);            \
        (v).data = NULL;               \
        (v).length = (v).capacity = 0; \
    } while (0)

/* ---------- typed API (exact names your code uses) ---------- */

#define blox_create(T) (blox_nil())

/* bytes_or_elems is BYTES in your callers; convert to elements */
#define blox_use_array(T, ptr, bytes_or_elems) \
    blox_use_((ptr), (size_t)(bytes_or_elems) / sizeof(T))

#define blox_make(T, elems) \
    blox_make_(sizeof(T), (size_t)(elems), 0)

/* resize length (grow capacity if needed; never shrinks capacity) */
#define blox_resize(T, v, elems)                               \
    do                                                         \
    {                                                          \
        __blox_resize_elems(&(v), sizeof(T), (size_t)(elems)); \
    } while (0)

/* lvalues / indexing */
#define blox_index(T, v, i) ((T *)((uint8_t *)(v).data + (size_t)(i) * sizeof(T)))
#define blox_get(T, v, i) (*((T *)((v).data) + (size_t)(i)))
#define blox_back(T, v) (*((T *)((v).data) + ((v).length - 1)))

/* push one element by value */
#define blox_push(T, v, x)                                        \
    do                                                            \
    {                                                             \
        size_t __w = sizeof(T);                                   \
        size_t __old_len = (v).length;                            \
        __blox_reserve_bytes(&(v), __w, (__old_len + 1) * __w);   \
        memcpy((uint8_t *)(v).data + __old_len * __w, &(x), __w); \
        (v).length = __old_len + 1;                               \
    } while (0)

/* push default-initialized element */
#define blox_stuff(T, v)                  \
    do                                    \
    {                                     \
        T __tmp;                          \
        memset(&__tmp, 0, sizeof(__tmp)); \
        blox_push(T, (v), __tmp);         \
    } while (0)

/* append raw bytes (used with T=uint8_t/char in your code) */
#define blox_append_array(T, v, src_ptr, nbytes)                                         \
    do                                                                                   \
    {                                                                                    \
        size_t __w = sizeof(T);                                                          \
        size_t __old_bytes = (v).length * __w;                                           \
        size_t __add_bytes = (size_t)(nbytes);                                           \
        __blox_reserve_bytes(&(v), __w, __old_bytes + __add_bytes);                      \
        memcpy((uint8_t *)(v).data + __old_bytes, (const void *)(src_ptr), __add_bytes); \
        (v).length = ((__old_bytes + __add_bytes) / __w);                                \
    } while (0)

/* append another blox of same T */
#define blox_append(T, v, other) \
    blox_append_array(T, (v), (other).data, (other).length * sizeof(T))

/* pop-front one element (O(n) memmove) — used for the TX queue front pop */
#define blox_shift(T, v)                                                             \
    do                                                                               \
    {                                                                                \
        if ((v).length)                                                              \
        {                                                                            \
            memmove((T *)(v).data, (T *)(v).data + 1, ((v).length - 1) * sizeof(T)); \
            (v).length--;                                                            \
        }                                                                            \
    } while (0)

#endif /* BLOX_H */
