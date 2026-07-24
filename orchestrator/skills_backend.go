package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type SkillDataPoint struct {
	Timestamp  int64   `json:"timestamp"`
	SkillName  string  `json:"skillName"`
	Value      float64 `json:"value"`
	Confidence float64 `json:"confidence"`
}

var (
	cacheData []SkillDataPoint
	lastFetch time.Time
)

func fetchSkillData(w http.ResponseWriter, r *http.Request) {
	// CORS Headers
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "application/json")

	// Cache in memory (latence < 1ms)
	if time.Since(lastFetch) < 5*time.Second && len(cacheData) > 0 {
		json.NewEncoder(w).Encode(cacheData)
		return
	}

	cacheData = generateMockData(1000)
	lastFetch = time.Now()
	json.NewEncoder(w).Encode(cacheData)
}

func generateMockData(n int) []SkillDataPoint {
	data := make([]SkillDataPoint, n)
	skills := []string{"Codeur (TDD)", "Scribe (Logs)", "Éclaireur (Search)", "RAG (ChromaDB)", "Ethique (RGPD)"}
	for i := 0; i < n; i++ {
		data[i] = SkillDataPoint{
			Timestamp:  time.Now().Unix() - int64(1000-i),
			SkillName:  skills[i%len(skills)],
			Value:      85.0 + (float64(i%15) * 0.9),
			Confidence: 0.95 + (float64(i%5) * 0.01),
		}
	}
	return data
}

func main() {
	http.HandleFunc("/api/skills", fetchSkillData)
	fmt.Println("🚀 Serveur Go High-Performance disponible sur http://localhost:8080/api/skills (< 1ms)")
	http.ListenAndServe(":8080", nil)
}
