// Host self-check: g++ -I src/thirdparty src/thirdparty/gbk_test.cpp src/thirdparty/sjis_converter.cpp && ./a.out
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "sjis_converter.h"

int main()
{
    char *s = gbk2utf8("\xd2\xb9\xcd\xed\xb5\xc4 abc \x81\xf4!"); // 夜晚的 abc ♪!
    assert(strcmp(s, "夜晚的 abc ♪!") == 0);
    free(s);
    s = gbk2utf8("\xff\xd2"); // invalid lead byte, truncated pair
    assert(strcmp(s, "??") == 0);
    free(s);
    return 0;
}
