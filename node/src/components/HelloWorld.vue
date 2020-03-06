<template>
  <div>
    <p class="subheading font-weight-regular">
      Permissions:
    </p>
    <li v-for="group in groups" v-bind:key="group">{{group}}</li>
    <br>
    <table>
      <td>Mapping access</td><td><p v-if="groups.includes('mapping | access')">YES</p></td>
    </table>
  </div>
</template>

<script>
export default {
  name: 'HelloWorld',

  data() {
    return {
      headers: [
        { text: 'test', value: 'group' }
      ]
    }
  },
  computed: {
    groups() {
      return this.$store.state.userData.groups
    }
  }
};
</script>
