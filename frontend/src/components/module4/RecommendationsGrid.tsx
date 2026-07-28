import { useState } from 'react'
import type { DestinationRecommendation } from '../../types'
import { getSimilarDestinations } from '../../services/api'
import { useAsyncAction } from '../../hooks/useApi'
import { RecommendationCard } from './RecommendationCard'
import { SimilarDestinations } from './SimilarDestinations'

interface RecommendationsGridProps {
  recommendations: DestinationRecommendation[]
  showBreakdown?: boolean
}

export function RecommendationsGrid({ recommendations, showBreakdown = false }: RecommendationsGridProps) {
  const [origin, setOrigin] = useState<string | null>(null)
  const similar = useAsyncAction(getSimilarDestinations)

  const openSimilar = (destination: string) => {
    setOrigin(destination)
    similar.execute(destination, 4)
  }
  const close = () => {
    setOrigin(null)
    similar.reset()
  }

  return (
    <>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {recommendations.map((rec) => (
          <RecommendationCard
            key={rec.destination}
            rec={rec}
            onSeeSimilar={openSimilar}
            showBreakdown={showBreakdown}
          />
        ))}
      </div>

      {origin && (
        <SimilarDestinations
          origin={origin}
          items={similar.data}
          loading={similar.loading}
          error={similar.error}
          onClose={close}
        />
      )}
    </>
  )
}
