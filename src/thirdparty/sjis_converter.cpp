#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "sjis_conv_table.h"
#include "sjis_converter.h"

char *sjis2utf8(const char *input)
{
    int len = strlen(input);
    // Shift-JIS won't give 4byte UTF8, so max. 3 byte per input char are needed
    char *output = (char *)malloc(3 * len + 1);
    int indexInput = 0, indexOutput = 0;

    while (indexInput < len)
    {
        char arraySection = ((uint8_t)input[indexInput]) >> 4;

        size_t arrayOffset;
        if (arraySection == 0x8)
            arrayOffset = 0x100; // these are two-byte shiftjis
        else if (arraySection == 0x9)
            arrayOffset = 0x1100;
        else if (arraySection == 0xE)
            arrayOffset = 0x2100;
        else
            arrayOffset = 0; // this is one byte shiftjis

        // determining real array offset
        if (arrayOffset)
        {
            arrayOffset += (((uint8_t)input[indexInput]) & 0xf) << 8;
            indexInput++;
            if (indexInput >= len)
                break;
        }
        arrayOffset += (uint8_t)input[indexInput++];
        arrayOffset <<= 1;

        // unicode number is...
        uint16_t unicodeValue = (shiftJIS_convTable[arrayOffset] << 8) | shiftJIS_convTable[arrayOffset + 1];

        // converting to UTF8
        if (unicodeValue < 0x80)
        {
            output[indexOutput++] = unicodeValue;
        }
        else if (unicodeValue < 0x800)
        {
            output[indexOutput++] = 0xC0 | (unicodeValue >> 6);
            output[indexOutput++] = 0x80 | (unicodeValue & 0x3f);
        }
        else
        {
            output[indexOutput++] = 0xE0 | (unicodeValue >> 12);
            output[indexOutput++] = 0x80 | ((unicodeValue & 0xfff) >> 6);
            output[indexOutput++] = 0x80 | (unicodeValue & 0x3f);
        }
    }

    // remove the unnecessary bytes
    output[indexOutput] = '\0';
    return output;
}

#include "gbk_conv_table.h"

// Chinese (汉化) data files store their text as GBK instead of Shift-JIS.
char *gbk2utf8(const char *input)
{
    const uint8_t *in = (const uint8_t *)input;
    char *output = (char *)malloc(3 * strlen(input) + 1);
    int o = 0;

    while (*in)
    {
        uint16_t u;
        if (*in < 0x80)
        {
            u = *in++;
        }
        else if (*in >= 0x81 && *in <= 0xFE && in[1] >= 0x40 && in[1] <= 0xFE)
        {
            // ponytail: 0x81F4 is SJIS ♪ (TH_SONG_NAME prefix); it shadows the rare GBK char 侓
            u = (in[0] == 0x81 && in[1] == 0xF4) ? 0x266A : gbk_convTable[(in[0] - 0x81) * 191 + (in[1] - 0x40)];
            in += 2;
            if (u == 0)
                u = '?';
        }
        else
        {
            u = '?';
            in++;
        }

        if (u < 0x80)
        {
            output[o++] = u;
        }
        else if (u < 0x800)
        {
            output[o++] = 0xC0 | (u >> 6);
            output[o++] = 0x80 | (u & 0x3f);
        }
        else
        {
            output[o++] = 0xE0 | (u >> 12);
            output[o++] = 0x80 | ((u >> 6) & 0x3f);
            output[o++] = 0x80 | (u & 0x3f);
        }
    }

    output[o] = '\0';
    return output;
}
