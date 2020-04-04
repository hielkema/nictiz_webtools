<template>
  <div>
    <v-container>
        <v-card>
            <v-subheader>{{title}}</v-subheader>
            <v-card-text>
                <D3LineChart :config="chart_config" :datum="results"></D3LineChart>
            </v-card-text>
        </v-card>
    </v-container>
  </div>
</template>

<script>
import {D3LineChart} from 'vue-d3-charts'
export default {
    components: {
        D3LineChart,
    },
    props: ['title','values','labels'],
  data() {
    return {
        loading: false,
        // Configuration
        chart_config: {
            values: this.values,
            date: {
                key: 'date',
                inputFormat: '%Y-%m-%d',
                outputFormat: '%d-%m-%Y',
            },
            tooltip: {
                labels: this.labels,
            },
            axis: {
                yFormat: '.1s',
                yTicks: 6,
                yTitle: 'Taken',
                xTicks: 5,
            },
            color: {
                scheme: ['#41B882', '#222f3e']
            },
            curve: "curveLinear",
            transition: {
                ease: 'easeLinear',
                duration: 1000
            },
        },
    };
  },
  methods: {
        
  },
  computed: {
    results() {
      return this.$store.state.TermspaceProgress.ProgressPerStatus;
    }
  },
  created() {
  }
};
</script>
