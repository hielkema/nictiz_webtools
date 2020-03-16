<template>
  <div>
    <p class="subheading font-weight-regular">
      Welkom <b v-if="user.details.first_name">{{user.details.first_name}}</b><b v-else>{{user.username}}</b>!<br>
      Kies in het menu een module om te beginnen.
    </p>
  </div>
</template>

<script>
export default {
  name: 'HelloWorld',

  data() {
    return {
      
    }
  },
  computed: {
    user() {
      return this.$store.state.userData
    }
  }
};
</script>
