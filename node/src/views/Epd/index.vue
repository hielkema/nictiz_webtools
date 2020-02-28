// EPD - index

<template>
    <div id="app">
        <h1>Test (static)</h1>
        <v-divider></v-divider>
        <v-container
        fluid
        >
            <v-row>
                <v-col class="col-2">
                    <PatientList />
                </v-col>
                <v-col class="col-7">
                    <PatientDecursusView />
                </v-col>
                <v-col class="col-3">
                    Samenvatting
                </v-col>
            </v-row>
      </v-container>
    </div>
</template>

<script>
import PatientList from '@/components/Epd/PatientList';
import PatientDecursusView from '@/components/Epd/PatientDecursusView';

export default {
    components: {
        PatientList,
        PatientDecursusView
    },
    data() {
        return {
            
        }
    },
    created() {
        this.$store.dispatch('Epd/getPatientList')
        this.$store.dispatch('Epd/getCsrfToken')
    }
}
</script>

<style scoped>

</style>