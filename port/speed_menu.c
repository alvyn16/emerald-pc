#include "speed_menu.h"

#include "port_ppu.h"

static unsigned sMultiplier = 1;
static unsigned sSelection;
static int sOpen;

void PortSpeedMenu_HandleEvent(const SDL_Event *event)
{
    if (event->type != SDL_KEYDOWN || event->key.repeat)
        return;

    const SDL_Keycode key = event->key.keysym.sym;
    if (key == SDLK_p)
    {
        sOpen = !sOpen;
        if (sOpen)
            sSelection = sMultiplier - 1;
    }
    else if (sOpen && key == SDLK_ESCAPE)
        sOpen = 0;
    else if (sOpen && key == SDLK_UP && sSelection > 0)
        --sSelection;
    else if (sOpen && key == SDLK_DOWN && sSelection < 3)
        ++sSelection;
    else if (sOpen && (key == SDLK_RETURN || key == SDLK_KP_ENTER))
    {
        sMultiplier = sSelection + 1;
        sOpen = 0;
    }
}

int PortSpeedMenu_IsOpen(void)
{
    return sOpen;
}

unsigned PortSpeedMenu_Multiplier(void)
{
    return sMultiplier;
}

static void Fill(uint32_t *pixels, int x, int y, int width, int height, uint32_t color)
{
    for (int row = y; row < y + height; ++row)
        for (int column = x; column < x + width; ++column)
            pixels[row * PORT_SCREEN_WIDTH + column] = color;
}

static void Glyph(uint32_t *pixels, int x, int y, const uint8_t rows[7], uint32_t color)
{
    for (int row = 0; row < 7; ++row)
        for (int column = 0; column < 5; ++column)
            if (rows[row] & (1 << (4 - column)))
                Fill(pixels, x + column * 2, y + row * 2, 2, 2, color);
}

static const uint8_t sLetters[][7] = {
    {14, 17, 16, 14, 1, 17, 14},  /* S */
    {30, 17, 17, 30, 16, 16, 16}, /* P */
    {31, 16, 16, 30, 16, 16, 31}, /* E */
    {30, 17, 17, 17, 17, 17, 30}, /* D */
    {4, 12, 4, 4, 4, 4, 14},      /* 1 */
    {14, 17, 1, 2, 4, 8, 31},     /* 2 */
    {30, 1, 1, 14, 1, 1, 30},     /* 3 */
    {2, 6, 10, 18, 31, 2, 2},    /* 4 */
    {17, 17, 10, 4, 10, 17, 17},  /* X */
};

void PortSpeedMenu_Draw(uint32_t *pixels)
{
    static const unsigned heading[] = {0, 1, 2, 2, 3};
    const uint32_t white = 0xfff2f2e8u;
    const uint32_t green = 0xff76df88u;

    if (!sOpen)
        return;

    Fill(pixels, 67, 17, 106, 126, 0xffe8e8e8u);
    Fill(pixels, 69, 19, 102, 122, 0xff242b38u);
    for (unsigned i = 0; i < 5; ++i)
        Glyph(pixels, 91 + (int)i * 12, 27, sLetters[heading[i]], white);

    for (unsigned row = 0; row < 4; ++row)
    {
        const int y = 49 + (int)row * 22;
        const uint32_t color = row == sSelection ? white : 0xffb6becbu;
        if (row == sSelection)
            Fill(pixels, 76, y - 4, 88, 21, 0xff43556bu);
        if (row + 1 == sMultiplier)
            Fill(pixels, 81, y + 4, 6, 6, green);
        Glyph(pixels, 105, y, sLetters[4 + row], color);
        Glyph(pixels, 119, y, sLetters[8], color);
    }
}
