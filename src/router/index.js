import { createRouter, createWebHistory } from 'vue-router'
import PodcastView from '@/views/PodcastView.vue'
import PodcastDetailView from '@/views/PodcastDetailView.vue'

const routes = [
  {
    path: '/',
    redirect: '/podcast'
  },
  {
    path: '/podcast',
    name: 'Podcast',
    component: PodcastView
  },
  {
    path: '/podcast-detail',
    name: 'PodcastDetail',
    component: PodcastDetailView
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router 