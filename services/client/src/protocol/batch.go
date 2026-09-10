package protocol

import "fmt"

const BATCH_PREFIX_BYTES = 2
 
func SerializeBatch(bets []*Bet) ([]byte, error) {
	totalBatchSize := 0
    for _, bet := range bets {
        totalBatchSize += BATCH_PREFIX_BYTES + len(bet.ToBytes())
    }
    batch := make([]byte, 0, totalBatchSize)
	lenBetsBytes := encode(len(bets), BATCH_PREFIX_BYTES)
	batch = append(batch, lenBetsBytes...)
	for _, bet := range bets {
        betBytes := bet.ToBytes()
        prefix := encode(len(betBytes),BATCH_PREFIX_BYTES)
        batch = append(batch, prefix...)
        batch = append(batch, betBytes...)
    }
    return batch, nil
}

func DeserializeBatch(data []byte) ([]*Bet, error) {
    if len(data) < BATCH_PREFIX_BYTES {
        return nil, fmt.Errorf("not enough data")
    }

    totalBets := decode(data[:BATCH_PREFIX_BYTES])
    idx := BATCH_PREFIX_BYTES

    bets := make([]*Bet, 0, totalBets)

    for i := 0; i < totalBets; i++ {
        if idx+BATCH_PREFIX_BYTES > len(data) {
            return nil, fmt.Errorf("not enough data")
        }

        betLength := decode(data[idx:idx+BATCH_PREFIX_BYTES])
        idx += BATCH_PREFIX_BYTES

        if idx+betLength > len(data) {
            return nil, fmt.Errorf("not enough data")
        }
        betBytes := data[idx:idx+betLength]
        idx += betLength

        var bet Bet
        if err := bet.FromBytes(betBytes); err != nil {
            return nil, fmt.Errorf("Error")
        }
        bets = append(bets, &bet)
    }
    return bets, nil
}