#ifndef __OLFACTORY_COMMON_H__
#define __OLFACTORY_COMMON_H__

#define STRINGIFY(x) #x

#define MIN(a,b) (((a)<(b))?(a):(b))
#define MAX(a,b) (((a)>(b))?(a):(b))

typedef uint8_t ol_bool_t;

#define OL_FALSE (ol_bool_t)0
#define OL_TRUE (ol_bool_t)1

#endif