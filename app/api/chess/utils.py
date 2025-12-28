class BackendUtils:
    @staticmethod
    def convert_moves_to_uci(legal_moves: list[list[list[int, int]]]) -> list[str]:
        def coords_to_uci(pos: list[int, int]) -> str:
            x, y = pos
            file_char = chr(ord("a") + x)
            rank_char = str(8 - y)
            return f"{file_char}{rank_char}"

        result = []
        for from_pos, to_pos in legal_moves:
            result.append(coords_to_uci(from_pos) + coords_to_uci(to_pos))
        return result
