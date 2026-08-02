import { createRouter, createWebHistory } from 'vue-router';

import Home from '../pages/Home.vue';
import Login from '../pages/Login.vue';
import Register from '../pages/Register.vue';
import Events from '../pages/Events.vue';
import Booking from '../pages/Booking.vue';
import Payments from '../pages/Payments.vue';
import Podcast from '../pages/Podcast.vue';
import Contact from '../pages/Contact.vue';

import Admin from '../pages/Admin.vue';
import AdminEvents from '../pages/AdminEvents.vue';
import AdminBookings from '../pages/AdminBookings.vue';
import AdminLogo from '../pages/AdminLogo.vue';
import AdminHomepage from '../pages/AdminHomepage.vue';
import AdminSettings from '../pages/AdminSettings.vue';

const routes = [
  { path: '/', component: Home },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/events', component: Events },
  { path: '/booking', component: Booking },
  { path: '/payments', component: Payments },
  { path: '/podcast', component: Podcast },
  { path: '/contact', component: Contact },

  { path: '/admin', component: Admin },
  { path: '/admin/events', component: AdminEvents },
  { path: '/admin/bookings', component: AdminBookings },
  { path: '/admin/logo', component: AdminLogo },
  { path: '/admin/homepage', component: AdminHomepage },
  { path: '/admin/settings', component: AdminSettings }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
