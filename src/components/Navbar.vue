<template>
  <nav class="nav">
    <div class="logo">
      <img v-if="logo" :src="logo" alt="Logo" style="height:32px; margin-right:8px;" />
      <span>? Traveling Star</span>
    </div>
    <div class="links">
      <router-link to="/">Home</router-link>
      <router-link to="/events">Events</router-link>
      <router-link to="/booking">Booking</router-link>
      <router-link to="/payments">Payments</router-link>
      <router-link to="/podcast">Podcast</router-link>
      <router-link to="/contact">Contact</router-link>
      <router-link to="/login">Login</router-link>
      <router-link to="/register">Register</router-link>
      <router-link to="/admin">Admin</router-link>
    </div>
  </nav>
</template>

<script>
export default {
  data() {
    return {
      logo: ""
    };
  },
  async mounted() {
    try {
      const res = await this..get("http://127.0.0.1:5000/api/settings/logo");
      this.logo = res.data.logo;
    } catch (err) {
      console.error("Failed to load logo:", err);
    }
  }
};
</script>
