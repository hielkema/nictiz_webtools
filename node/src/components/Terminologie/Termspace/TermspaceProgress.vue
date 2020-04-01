<template>
  <div v-if="user.groups.includes('mapping | access')">
    <v-container>
      <v-row>
        <v-col>
          <v-card class="ma-1">
            <v-card-title>
              <span class="headline">Voorraad (data)</span>
            </v-card-title>
            <v-card-text>{{results}}</v-card-text>
            <v-card-actions></v-card-actions>
          </v-card>
        </v-col>
        <v-col id="arc">
            <D3LineChart :config="chart_config" :datum="results"></D3LineChart>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import {D3LineChart} from 'vue-d3-charts'
export default {
    components: {
        D3LineChart,
    },
  data() {
    return {
        loading: false,
        chart_data: [
            {hours: 2092, production: 1343, date: 2003},
            {hours: 2847, production: 1346, date: 2004},
            {hours: 2576, production: 1233, date: 2005},
            {hours: 2524, production: 1325, date: 2006},
            {hours: 1648, production: 1456, date: 2007},
        ],

        // Configuration
        chart_config: {
            values: ['SemanticProblem', 'Medisch', 'CAT incomplete'],
            date: {
                key: 'date',
                inputFormat: '%Y-%m-%d',
                outputFormat: '%d-%m-%Y',
            },
            tooltip: {
                labels: ['Semantisch / Problem', 'Medisch', 'CAT incompleet']
            },
            axis: {
                yFormat: '.1s',
                yTicks: 6,
                yTitle: 'Lorem ipsum',
                xTicks: 5,
            },
            color: {
                scheme: ['#41B882', '#222f3e']
            },
            curve: 'curveLinear',
            transition: {
                ease: 'easeBounceOut',
                duration: 1000
            },
        },
    };
  },
  methods: {
        
  },
  computed: {
    user() {
      return this.$store.state.userData;
    },
    results() {
      return this.$store.state.TermspaceProgress.results;
    }
  },
  created() {
    this.$store.dispatch("TermspaceProgress/getProgress");
  }
};
</script>
