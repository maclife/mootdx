# encoding=utf-8

import struct
import sys
from ctypes import *

import pandas as pd


### take ref this article :http://blog.csdn.net/fangle6688/article/details/50956609
### and this http://blog.sina.com.cn/s/blog_6b2f87db0102uxo3.html
class GbbqReader(object):

    def get_df(self, fname):
        if sys.version_info.major == 2:
            bin_keys = bytearray.fromhex(self.hexdump_keys)
        else:
            bin_keys = bytes.fromhex(self.hexdump_keys)
        result = []
        with open(fname, "rb") as f:
            content = f.read()
            pos = 0
            (count,) = struct.unpack("<I", content[pos:pos + 4])
            pos += 4
            encrypt_data = content
            # data_len = len(encrypt_data)
            data_offset = pos

            for _ in range(count):
                clear_data = bytearray()
                for i in range(3):
                    (eax,) = struct.unpack("<I", bin_keys[0x44:0x44 + 4])
                    (ebx,) = struct.unpack(
                        "<I", encrypt_data[data_offset:data_offset + 4])
                    num = c_uint32(eax ^ ebx).value
                    (numold,) = struct.unpack(
                        "<I",
                        encrypt_data[data_offset + 0x4:data_offset + 0x4 + 4])
                    for j in reversed(range(4, 0x40 + 4, 4)):
                        ebx = (num & 0xff0000) >> 16
                        (eax,) = struct.unpack(
                            "<I", bin_keys[ebx * 4 + 0x448:ebx * 4 + 0x448 + 4])
                        ebx = num >> 24
                        (eax_add,) = struct.unpack(
                            "<I", bin_keys[ebx * 4 + 0x48:ebx * 4 + 0x48 + 4])
                        eax += eax_add
                        eax = c_uint32(eax).value
                        ebx = (num & 0xff00) >> 8
                        (eax_xor,) = struct.unpack(
                            "<I", bin_keys[ebx * 4 + 0x848:ebx * 4 + 0x848 + 4])
                        eax ^= eax_xor
                        eax = c_uint32(eax).value
                        ebx = num & 0xff
                        (eax_add,) = struct.unpack(
                            "<I", bin_keys[ebx * 4 + 0xC48:ebx * 4 + 0xC48 + 4])
                        eax += eax_add
                        eax = c_uint32(eax).value
                        (eax_xor,) = struct.unpack("<I", bin_keys[j:j + 4])
                        eax ^= eax_xor
                        eax = c_uint32(eax).value
                        ebx = num
                        num = numold ^ eax
                        num = c_uint32(num).value
                        numold = ebx

                    (numold_op,) = struct.unpack("<I", bin_keys[0:4])
                    numold ^= numold_op
                    numold = c_uint32(numold).value
                    clear_data.extend(struct.pack("<II", numold, num))
                    data_offset += 8

                clear_data.extend(encrypt_data[data_offset:data_offset + 5])

                (v1, v2, v3, v4, v5, v6, v7,
                 v8) = (struct.unpack("<B7sIBffff", clear_data))
                line = (v1, v2.rstrip(b"\x00").decode("utf-8"), v3, v4, v5, v6,
                        v7, v8)
                result.append(line)
                data_offset += 5

        df = pd.DataFrame(data=result,
                          columns=[
                              'market', 'code', 'datetime', 'category',
                              'hongli_panqianliutong', 'peigujia_qianzongguben',
                              'songgu_qianzongguben', 'peigu_houzongguben'
                          ])
        return df

    hexdump_keys = "38 A7 C2 1D E0 6A 17 E2 D1 39 A2 40 9C BA 46 AF 42 C6 FF 05 74 EA DA BB 89 B4 F8 44 AC 89 D7 F2 98 7F B6 BC E4 F7 6B 75 05 04 58 67 79 C8 6D C6 2B 06 96 8C FB 86 06 8B BF D6 E8 E1 87 49 6B 36 C7 18 02 79 53 25 72 72 13 CC 04 0B 90 24 0C DC DB 03 1A D5 2E 04 85 5C 7E 8E BD 02 26 2D BD 06 1B 50 34 99 1B A2 24 04 F2 88 35 C8 89 EA D5 FB 12 24 BB B5 3B 29 CA 14 A6 04 CE A9 A8 58 02 B9 AA E3 97 A3 A6 22 57 BB AD A0 22 5F EB 05 86 11 C3 ED B1 3F 39 C2 36 D1 4A 43 C8 64 4D B0 6E 3A 7C 51 6D F7 8E C6 DF F3 8E A4 1E 74 9D B2 22 05 4D 07 3F 96 7F 97 F9 63 B9 C4 2B 98 75 F6 D6 84 56 DC 15 D3 52 8B 60 F3 D6 0E A9 AD 07 07 E9 02 86 58 C2 32 9C 90 BC C9 19 BF B0 54 7A F8 CC A8 27 63 82 29 EE FB 98 11 BF 35 29 62 91 93 95 FC F4 F0 08 E4 B2 3A B4 5E B3 B0 2E 3E 20 C1 D7 43 59 7D C6 29 5F 69 74 7F B2 77 E1 0E FA 85 A1 C9 77 73 83 B3 CB 1C 60 DB E9 53 69 FC B3 18 59 15 0F 97 8A 7A C8 83 F5 49 DC 1B 3E 86 C1 95 45 46 E2 16 67 7F 12 35 A0 BB 27 FB CC F8 30 7E 4F C8 6D AB 18 B2 0D 01 CC 79 20 80 7B FA 37 AA 14 9E 85 E8 25 E9 D4 2D 35 4E 8F D3 DE B0 06 8D 15 15 52 65 E8 39 03 28 09 02 67 99 3D 13 BA F3 68 5C 4C 89 B0 E3 6B AE 16 5C 88 25 F8 33 03 19 02 5B 29 7B 2A 41 2D 75 49 48 9B B3 B6 B3 BF AA DF 8C 95 FE 0F 13 B8 7B 02 BB 52 E1 1C 34 C3 9B 87 59 E2 46 CC 22 77 4B D7 C4 2C 31 AA 84 7C 44 51 88 15 1A CC AE 40 9D 1F 44 97 29 98 45 60 74 47 A1 0D A5 73 F0 53 FF 01 F9 F4 9A F1 36 07 D0 2D A0 79 2D 81 23 25 AD 4B 9C C8 BC 12 55 4D D4 BB 95 B1 B9 BE 7D A6 E6 A0 53 BA 83 8C DD 7E E9 4B ED BA 28 42 D8 FF 98 69 35 CA 4E 9C 9D 57 D6 CF A0 89 5C A2 E7 54 D2 AF 4C FB 54 C4 B4 4F C3 BA F8 A2 58 69 19 79 0E A8 0E 3D C8 04 FD 26 32 C8 E1 02 8B A7 1C C3 91 25 E5 D8 49 DB DF 19 5F 16 F5 A7 8B 18 23 04 D4 BF FB 44 C4 61 7C 79 6E C8 90 15 B5 EB 50 87 CA 7A 69 47 2F AF A8 B5 A2 8A 84 C4 41 79 E8 DE 0C AC D0 D5 6F 34 C6 CB A7 76 F9 00 24 42 05 26 7E 7B 14 86 59 7B DB 1C 62 D5 B7 3E F7 17 44 27 4B D2 C6 6F FF C8 49 55 AD 65 52 2D 43 C2 33 9B 63 AB 3D 54 54 28 E2 02 65 03 9A 03 4B 8F 64 1A 92 52 DE 32 D6 2B F0 BE BE 1D 54 B1 7C 70 41 9B 90 55 DA 71 55 21 B9 B6 68 90 19 5F BC AA B4 55 0E E6 81 4C A3 BE BC 64 D7 59 00 59 BD 0F 6A 57 1A A6 A0 D5 1A 0A 80 D3 09 06 73 5A 51 E2 DD 29 66 AC A0 86 29 21 2B 7A 6D 9E 3A 68 D0 A3 DC A7 2B 85 A0 4C D4 F0 C5 C4 43 E4 CF 0C 19 81 30 B6 F6 BE 71 F5 AC 25 AA CF 42 90 06 64 1B 45 29 FD 3A A3 B6 0B 9D 29 9F FA 31 B8 6D D8 EC 43 F5 92 7E 35 22 E0 C3 D3 09 06 61 71 DA E8 36 0A 19 F6 23 81 CB 89 E0 67 6E FE B1 E6 47 72 63 5C 25 18 E0 B4 65 85 EF B5 1B 26 23 90 89 CC EE E3 01 77 95 63 DF C4 AC BF E6 37 14 99 15 49 8A 96 02 91 AA 1D 98 21 57 5E 87 96 C7 B5 87 08 3F 58 06 52 58 17 8F AB A8 4E A1 7A 60 B1 69 5E 9C BE E2 D0 C5 12 59 DF 31 EB D2 19 54 96 E2 10 11 8E 68 B4 1A 2D D3 2F AB 12 F7 FE F3 A7 F7 61 FC F7 7C CB FC 87 8C 6A 10 40 29 7B 30 D6 0D 13 4C 71 CD 5E AB 36 A2 F1 4C 05 ED 53 88 E5 FF 8E 71 79 5D B5 AF D3 67 6D C4 44 6B AB C1 A7 AA 38 D8 70 1E 08 E6 D2 36 7B 88 11 96 DB D2 68 D9 FF D8 50 2B 3A A9 CC 45 1A CA CD D2 05 C6 FC A0 35 0C EE 98 2B 5C B2 39 6A 27 12 8F 97 EC CB 7B B6 C0 27 F6 A7 48 75 09 82 98 CA 3A 5D E3 96 0C A5 D2 B3 6C A4 D1 1F AE 99 67 B0 3D D6 9A 7A 3E 00 8B FD 45 32 F7 9F 28 7C 94 03 DB 64 AA 44 80 D2 27 AF B3 73 87 57 31 EB 08 D9 BA 73 4D 2C 77 03 BF F5 0F 47 3C 22 DA 3F B9 F1 9A 1B 22 83 16 EE F4 18 FC 08 E8 3B 30 1C 04 50 AA 4C E3 28 53 AB DE F8 5F 32 D9 E1 78 7B F1 C5 A8 CA 85 B6 9F 89 1F 40 B8 2C 88 D7 C1 66 34 45 D6 46 FD 7B F3 72 A3 32 55 23 CF B5 B0 79 AB A0 F1 00 5C DB EE 3F 51 AA AE C0 89 8E 47 A5 30 4E 4B DD D6 AE D8 6D 40 1C 4E 8E FB 0C 60 8D 54 1E 2F 17 B7 3A ED DE DC 81 F5 72 85 B7 A6 39 31 6F 47 50 84 43 C5 11 F3 6A 26 8E BA 7F 81 98 31 FD 13 6B 83 C9 11 61 48 64 FA E3 F5 39 2C 12 11 C1 6D 4D 03 13 A6 C2 E0 DF F5 32 8E 5B 35 A7 7F 08 F7 85 27 0D 71 9D B8 CE 9C 1E BA 77 3A F6 A1 A7 26 94 29 C0 20 10 65 75 6E EF AA 32 0C 66 91 3A 4E 0E 74 E2 8A FE B6 F8 17 C7 A7 E4 D8 35 67 2E F0 83 A8 9F A6 28 13 40 A3 96 DC 49 83 55 E1 85 AB BD 4D ED 88 FA 36 69 A9 77 59 5A 9C D0 A0 B1 3D EB 31 16 DC 3E 29 7B 39 01 5B D4 FF 5C E5 9E DA F7 55 D5 3F E3 3B 51 76 83 8E 40 AE E1 2E E8 3E F8 08 B7 B0 24 26 91 AD 82 4C 2E 2F 37 7A 34 A1 05 BD 8C 9A 75 52 5C CD 59 80 CB 92 F8 B1 F8 A5 F2 2C 9F 4A 59 BF EF 76 A3 74 4F E1 C9 7C 7F 91 D9 0D 12 05 B2 8E D0 E0 BB 46 D4 5C 44 2F 65 6D 7A 1C 02 86 FB 7E 7D B6 2A 57 B9 DB 80 CD 02 BF E7 9E 35 21 FB BE 28 13 82 9F F0 74 F7 92 55 DE F2 7B F2 F2 7D F5 A0 14 0F 99 4D 25 F4 DC 11 17 7A 77 65 77 CC BE EF 90 88 E8 FD B2 4E 8E F5 26 FE 53 5D 65 A9 74 47 0B CB E9 E8 71 95 95 87 6C FD 86 94 A7 E5 FC 20 00 1E 0A 0A E3 85 17 24 D4 D0 73 8A 11 1E 1E EF 83 E3 D7 E1 BF CC 98 07 6D 70 37 3A 8F 31 17 55 4E 60 A8 C8 AB 4F 08 2D 37 76 E6 2B 58 DD 81 0F D1 6E 9A A6 55 3D 80 82 99 9E 2D 16 9A DF 4E CB 3B 5D DA A8 53 08 C7 FF 54 DD C6 11 31 1A B6 EB A3 03 08 4A FB B4 45 EC C0 7C 0D C6 CF CB 1B 78 46 88 8F F4 6A 15 62 2F 17 12 E6 41 64 76 58 96 78 DB 29 B5 6A AE DE 63 41 6F BE 9B 37 6C C9 D0 EC 1B F6 79 17 9E FE 79 0E B1 82 28 F2 06 15 C2 BE 96 9C E0 81 80 D7 00 DB 95 87 4B C0 0D 91 55 5B 1F 86 22 64 74 EA 1B 89 85 D2 DD F7 9F F1 D9 09 06 64 FA 6D 59 72 EF CE 66 A7 03 D1 99 E8 DF AE D7 63 5F 60 5F AB 6E C5 22 C8 3A 94 6A 3B 00 72 F8 DB 90 E7 05 DC A2 89 0F 83 AA 03 FE 42 14 1C 8A E6 1C 9E DB D8 D0 CA 97 21 6C AD ED 0A E0 A2 9E EC C1 FF D1 B4 8A 9A AD AB 34 0B 13 3F B5 18 8D 85 9E 0D F9 FB AC 21 2E DD 7A DE BF 9F 7E BD BF 84 DF F5 FD 1E BE E1 1F 0F F8 18 9D 73 09 02 29 B7 5B 26 7E 44 75 04 4D B1 AA 2F 3A DB 46 38 12 D1 41 35 91 29 06 DF C9 98 69 92 02 F2 48 12 A9 71 D2 AE 3B 23 6D 1C E2 6B 8B 75 87 4A 13 A7 1F 81 4D 29 65 53 0A 3A 34 CE 6D E6 31 8D 7E 4E DD 25 6E 76 44 82 3C 47 36 4C B9 C4 9B F4 4F 84 43 11 56 C2 94 53 7E B0 2E 36 DA EB 77 5F C1 64 E2 CA 9F BE 29 D8 06 36 53 D0 6F 82 19 DA BC 8C 5F 4D 45 E7 21 37 9E 90 A6 D4 33 A8 64 4D EC BC 90 5E FE 8E 8B CA 17 7C FF AC 96 BB 21 CF 3D 24 71 3B C2 A1 74 68 85 CF 32 8E 7F 63 39 C5 E7 8E A5 E0 CD 3A F5 9A B8 FD 43 D4 43 39 08 8E 45 76 5F DF E9 17 54 59 12 ED D0 E9 3D 6F 3F 02 14 8A 0A 47 9A D1 E7 FA 4E A1 41 00 50 EF 60 9D 4D C1 CA 87 98 40 E7 B2 0F 76 C0 9D 71 EF D7 46 93 C1 2B 9F 11 B8 F9 05 AC ED A7 72 6B F5 11 9B 3E 0A 04 21 7D 06 D7 46 76 7B AD AE 9D 95 A6 47 68 05 AD F5 38 7C C7 A5 5A CA B2 CB 48 18 C1 F2 62 55 98 36 39 08 80 C5 28 B1 06 E4 FB 46 11 3C 38 A1 4F 1C FE A1 81 B7 FC DB 94 B0 7A FE B5 74 F1 BB 92 AA FF B0 FE 1E 31 8B C6 BC F0 4F 1A FE 91 C5 7A 9C 73 09 4A 32 90 51 01 8B 12 C0 20 CA 3C CB 14 83 D3 C7 7C 5A 12 79 EE 56 1A 36 C4 09 E2 3E DC E8 CE F1 C1 A1 9E 99 DA 64 4F CF 1E D6 2B 70 27 86 3E CF BE 75 1C 39 9B F9 53 63 C1 6B 58 CC 71 D2 07 41 88 BB 14 70 96 F1 68 CE 13 75 FE F4 A0 C8 85 A2 67 18 49 56 0D 07 94 1D 74 61 89 0C 32 49 9D 0D 94 73 4A AB 1A E9 0F E0 BA B6 4A 34 F9 33 1D B3 71 C2 B8 64 D7 0B CB 19 F7 BD E0 69 3E 24 96 B1 C4 28 09 5F 58 AE 8A C0 83 99 19 64 4D 44 37 55 A6 9B A1 42 50 84 B8 18 29 B5 21 91 58 23 88 EB 8F 13 4A 24 09 EC 0F 6D 7D AF 3E FC F7 F3 9F 34 39 15 C4 84 03 BB 7E 67 39 5F 2A 2C 67 94 F4 A6 B5 02 3F 45 56 79 0C 2A 9B 25 77 67 C2 3B CC F2 71 3B 4F 83 2A 8D 8C 53 0D 18 49 54 CA 58 0E BE 8B 3A 53 74 FC 6F 47 28 07 8E C1 F5 53 D3 34 4B 08 05 FF E9 14 29 40 1B 57 AD 77 EC E8 DA DA 35 55 A7 78 03 56 4C 7C B2 ED 3B B5 61 65 91 DF 41 B4 5D C9 B7 9B 13 82 41 15 D7 B3 6E 1C C8 15 B4 F0 F3 3F 91 4B A1 C8 90 78 91 39 5A 21 55 DA 6A E1 2C BA C9 38 69 F6 AE A8 2B 8C B7 14 C1 35 82 35 A0 78 47 56 C0 9A A7 7F 74 14 64 85 F1 B7 48 BC 55 8C 6A A4 95 1C CB F3 52 F9 54 61 15 27 56 43 D0 27 95 E3 35 AA 39 DC 23 38 DA EF 1F 27 65 3A AB F7 CC BB 25 DB 00 36 34 96 D1 F7 C4 EC 44 37 42 7E 17 18 67 C8 9C 9A 5B 39 08 5C 3C F4 92 F1 16 31 88 FA 12 44 9E 79 27 1C C2 0B 46 AC CD 1F 39 B8 9F 9A 56 34 0A 85 86 C2 B1 B1 9B 31 CE 47 57 05 3E A7 AE 3F 3E 01 2D C5 B9 C1 CB BA AB 0A 2A D2 71 E4 EC F8 0A 71 85 CC A1 CA 6E EF 9D 87 22 38 5D 80 81 F7 1A 6C 31 7B 82 86 BD 7F 10 9D 89 B6 F7 AF E4 41 0D 4F 97 28 80 34 06 3E 19 3A 21 60 ED 54 18 02 0F 2F D5 D5 3B A5 87 01 21 38 1B A6 99 32 28 E9 8D 6F 02 35 60 85 BD 64 C4 B0 26 7E 68 D1 E6 97 B5 32 6E B2 4F EB 06 4C 4D C2 97 8E 6B 30 22 C0 B4 3D 47 93 78 67 AC 27 42 DD 5C 3C 27 ED 0A 6C E4 4A 0D 0F DF 52 63 A6 70 76 09 F0 2E 58 F6 05 B2 DF EE C9 1F CB 1D 11 0C A1 8B 19 26 B8 10 2C 81 48 FF 98 EF 30 36 0C 01 C5 4A D9 AC 05 72 89 C7 3F D6 4D E0 17 BA BA B3 D3 E8 1B 0C 8C C8 DF 6B FE 7E BA 91 FD F6 A0 CB 59 19 B0 01 2F D7 0B A0 62 0F 5F CE 74 B8 EB 42 89 B5 BE CA C9 EF DA 9A BB C6 66 1B E0 65 EE D4 3A CE D9 CC 0E BB 85 50 41 45 01 BA 1B 29 11 6F 34 11 55 03 DD 0C B5 99 56 3A 93 4D 4D 95 6D CE C3 51 E0 15 54 3E FF 2F A3 DA 59 EC 3D 59 2D 62 FC 64 39 D6 7B C8 80 78 1D D7 FD E8 0B 5D 8A ED 1A 9D 98 CB C2 EE 78 47 30 AD 8F 64 A5 82 12 23 DA B3 3E CA 4C 85 7A 80 D5 9F 46 20 D6 EE D1 F9 33 FA 1F C5 9C 8E F9 1E 66 51 A5 46 68 DC B7 7F A8 5A DE E6 18 D7 8C 2B 5D EA A8 EC 6B 8B 48 C1 92 5A C1 B1 6A 5E 37 82 22 4B 6A B6 F0 40 16 89 16 A5 81 F8 D4 1B 20 26 86 35 E5 AD C1 01 6E C9 B5 D0 69 C5 0B 31 08 51 5D 35 FC 74 F5 13 04 7A F4 57 10 53 5B A4 CC 8B 21 82 82 15 4B 8C 3D 6B DA 91 85 CB D6 CF 05 80 D0 F0 CF 0D DF 7A B4 99 C7 F8 D5 4C 76 56 30 E9 65 B6 58 60 C1 C0 39 8A 42 54 BC 4A 48 8B A1 D9 5C 32 05 7A 1C BB 50 51 5B 7F C7 75 2D 68 55 E6 83 7B C3 98 FD E6 D5 B8 DA A8 31 01 78 F5 60 8B 1A D2 FD 51 34 47 FA AF 23 AE E2 DE 15 A7 07 66 69 35 9A 40 61 55 25 98 23 54 2A 50 C9 7D A6 CE 74 F8 19 0C 8E 63 E5 49 2F F9 17 05 FD 39 15 55 F4 B0 91 BF 60 B7 B2 40 2E 7A D3 68 86 C0 FC 38 88 AB B9 03 8A 04 05 1A 9F 61 AE F2 D3 B8 A4 29 F8 51 43 CF 84 26 4A 90 6E 13 27 AF 7B 52 DB F9 00 E8 AE C0 B5 6F 64 03 57 20 59 7C F5 E1 65 A8 47 C3 BD EE 72 2A 85 E2 70 8D EA 9D 98 D4 2A D5 70 A2 E9 76 A2 DA E6 7C B0 F7 14 D9 23 B6 88 C0 B3 6F 42 12 F4 69 0C 15 81 D6 F7 0B B7 1B DF 15 E6 75 63 13 53 B3 20 43 79 90 34 E3 34 48 80 D6 86 BB 45 A2 85 DD F8 23 64 3B D5 68 AB 99 53 34 C6 25 0A 87 73 17 37 56 39 BA 8C 0E 39 24 4B CC AA 98 84 0C 2F 27 E6 E2 AC 86 34 5D 1E 25 AE FD 1E FF 3C 27 AD 26 18 4A 1A E5 09 61 5D 83 5F 2C DC 41 A7 C6 07 55 5B B5 0B 71 FE 86 E7 30 A1 BC 27 AF 5F 24 51 1A DD 20 F6 32 9E 3D 64 6F DC 43 65 2A 80 CB 95 C4 B6 F0 E1 F3 CF 6C F2 C2 9C EA 81 88 0C 2D D2 DA 74 82 C6 A5 1E 98 D3 BC 71 ED E2 0B 05 DA BB 0E FA 35 0A 2C D5 C8 62 E7 B1 AF 95 14 6C 83 7D F1 CE 9F 13 6B D8 68 C9 A5 F5 87 2E A5 8F D7 5C B2 C6 99 37 31 5A A4 D0 E2 43 DF C8 BE BD 10 C0 D8 22 63 95 46 1E E7 8C A8 61 E4 74 02 6C B4 30 F3 06 15 11 E6 2A 3A 0D 3B 2F B9 3B B3 83 40 18 79 FB 39 38 B7 CE 4D BA F6 9E AA E1 8F 32 1C B1 68 DD 5C 2C 37 65 61 73 3D C6 34 56 CD EA BC 77 6A A1 7D 6A F1 F9 78 AF 0F D9 C2 AA D3 D7 A8 2D A8 6E BC 19 83 96 B5 A3 3E B3 B2 5C 54 AD 77 CE 1D E5 D5 AA B3 0D 36 7A 32 7D 5C A3 60 66 8D 84 A0 BD 4F 0F A9 09 89 B8 EC 14 8A 2B 2B 74 8E 75 77 5A 8E B2 51 D0 26 D6 06 8C 9A CA 31 D6 94 17 F0 14 D7 43 1C 82 0C 00 83 E6 75 05 5C 52 AB 0C 38 8F A3 35 77 52 E8 3E 3B CB 48 81 E3 25 B1 A9 40 12 76 4F 16 F1 CE 3D D7 23 89 44 D7 3F 24 7E B7 46 66 C1 16 7A 17 B2 2A 99 F1 AC 3C C9 9D C5 FE 89 BE BF 2C 68 BC 2C A7 F1 C5 2F 26 1E CC D1 AF 7D AA 7D C5 94 4A 4D C4 87 97 2D 2B 6A 5E 5E BF 39 82 18 AB 8C B9 DC 80 83 A1 D1 80 D2 65 FE 2E CC 6A F1 02 84 B2 36 60 37 24 4E 5E 57 AD A5 C5 50 1A 5E A4 5C 31 B6 93 60 57 AC EB ED 65 3F BF EA C7 08 CA 13 00 93 E5 E6 79 F6 37 20 CA B4 6E 39 9E 83 4F 15 8B 15 CD E7 8C 90 93 B0 85 91 9B AE 21 EF 03 D0 A4 B6 2A B4 C6 D3 07 04 92 54 72 8E EC 2E B3 47 6C CE 42 06 7F E0 5B 96 F2 48 8B FA 8F 83 E2 47 10 A5 B7 30 F8 68 B0 FD 02 74 6F 48 71 D7 F1 2E DF A1 52 61 76 99 47 BE 0A 2F F8 F2 69 9D AD 03 FA E6 84 A7 CF 35 7D 8F 5F C5 A6 9B 21 66 35 BC 58 D5 89 B5 E0 9F 11 F0 A8 8A 1F C8 3C 24 B2 B7 F1 6C 8A DB 3B 39 7A CA D0 EF 15 61 22 72 FD FC 02 3D BD 76 35 9E E1 C6 D7 2C B2 59 E1 03 E0 FF 7A 87 03 79 9F 61 AB CC 49 98 C2 41 CF 6E 9B AA 52 9B D0 08 B5 9E 23 F6 C1 39 82 77 16 5D D4 E1 B3 AD A0 0C 58 F8 E2 67 00 6A 0B 4B D2 6C E1 C5 6B 9D BA 3F 40 82 C5 28 B8 C1 60 75 85 EE C4 FA 04 ED 62 64 B6 29 10 67 4B 9B D6 6C 0E 06 62 64 83 CA F0 2F 2D B8 F6 0A D7 D7 6A 1C 58 14 BE 18 60 80 29 02 CD F6 B1 95 A5 6D 2E 27 9C 08 E3 1F C5 C2 07 7F 63 7F DB 82 C6 C6 85 AC A6 D2 4C F1 7F DB 1D CF 86 20 56 60 C0 24 E0 C0 42 0B 4E 00 5F 8B 78 60 FE EA EC 6D 31 93 49 70 EB 2A 45 4F 92 9B 6C 17 28 BB 89 FC C0 07 84 CC AD 1B 85 F2 85 18 5C 3D 5A 60 54 AF 03 9D 9E E4 26 D3 86 AA 0B 7C A3 32 9C C2 0F 3A D4 3E 1F 52 43 A8 31 E9 70 FC 0C B4 7C F5 E3 C7 6F 11 ED 22 4C 0C 1B 82 CB 72 A4 95 28 1A D4 1B E5 C4 6E D7 F1 EC BF 25 2C B8 92 87 A8 D2 15 79 34 39 C0 BE 0D C8 68 2D F2 D3 8E 01 09 3C 48 94 32 69 89 D5 C0 5D E8 2C E6 A6 97 59 4B 9A C6 61 B0 9E DB 81 DC D3 F9 47 34 84 00 CA 87 BE 5D 6D 56 F3 01 02 3B FF FF FF FF 00 00 00 00"


if __name__ == '__main__':
    result = GbbqReader().get_df("/Users/rainx/tmp/gbbq")
    print(result)
