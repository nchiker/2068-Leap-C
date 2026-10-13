// 40 sparse cases and 40 dense ones in one switch each.
// expect: exit 0
int sp(int v)
{
    switch (v) {
    case 7: return 1; case 19: return 2; case 31: return 3; case 43: return 4; case 55: return 5;
    case 67: return 6; case 79: return 7; case 91: return 8; case 103: return 9; case 115: return 10;
    case 127: return 11; case 139: return 12; case 151: return 13; case 163: return 14; case 175: return 15;
    case 187: return 16; case 199: return 17; case 211: return 18; case 223: return 19; case 235: return 20;
    case -7: return 21; case -19: return 22; case -31: return 23; case -43: return 24; case -55: return 25;
    case -67: return 26; case -79: return 27; case -91: return 28; case -103: return 29; case -115: return 30;
    case 1007: return 31; case 2019: return 32; case 3031: return 33; case 4043: return 34; case 5055: return 35;
    case 6067: return 36; case 7079: return 37; case 8091: return 38; case 9103: return 39; case 30115: return 40;
    }
    return 0;
}
int de(int v)
{
    switch (v) {
    case 100: return 1; case 101: return 2; case 102: return 3; case 103: return 4; case 104: return 5;
    case 105: return 6; case 106: return 7; case 107: return 8; case 108: return 9; case 109: return 10;
    case 110: return 11; case 111: return 12; case 112: return 13; case 113: return 14; case 114: return 15;
    case 115: return 16; case 116: return 17; case 117: return 18; case 118: return 19; case 119: return 20;
    case 120: return 21; case 121: return 22; case 122: return 23; case 123: return 24; case 124: return 25;
    case 125: return 26; case 126: return 27; case 127: return 28; case 128: return 29; case 129: return 30;
    case 130: return 31; case 131: return 32; case 132: return 33; case 133: return 34; case 134: return 35;
    case 135: return 36; case 136: return 37; case 137: return 38; case 138: return 39; case 139: return 40;
    }
    return 0;
}
int main(void)
{
    int i;
    if (sp(7) != 1 || sp(235) != 20 || sp(-7) != 21 || sp(-115) != 30 || sp(30115) != 40 || sp(8) != 0) return 1;
    for (i = 0; i < 40; i++) if (de(100 + i) != i + 1) return 2;
    if (de(99) != 0 || de(140) != 0) return 3;
    return 0;
}
