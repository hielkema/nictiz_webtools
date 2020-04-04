<template>
  <div>
    <v-container>
        <v-card>
            <v-subheader>{{title}}</v-subheader>
            <v-card-text>
                <apexchart  type="line" height="400" :options="options" :series="seriesFiltered"></apexchart>
                <v-expansion-panels>
                  <v-expansion-panel>
                    <v-expansion-panel-header>Selectie</v-expansion-panel-header>
                    <v-expansion-panel-content>
                      <v-checkbox 
                        dense
                        v-model="selection" 
                        v-for="series in chartSeries" 
                        :key="series.name"
                        :label="series.name" 
                        :value="series.name"></v-checkbox>
                    </v-expansion-panel-content>
                  </v-expansion-panel>
                </v-expansion-panels>
            </v-card-text>
        </v-card>
    </v-container>
  </div>
</template>

<script>
export default {
  components: {
  },
  props: ['title'],
  data() {
    return {
      selection : [
        'e.degroot total open',
        'krul total open',
        'mertens total open',
        'soons total open',
        'paiman total open',
        'hielkema total open',
        'timmer total open',
        'krul total open',
        ]
    };
  },
  methods: {
 
  },
  computed: {
    seriesFiltered() { 
      var that = this
      var output =  this.chartSeries.filter(function(series) {
        return that.selection.includes(series.name);
      })
      return output
    },
    options: function() {
      return {
        theme: {
          palette: 'palette2'
        },
        chart: {
          id: 'vuechart-example',
          dropShadow: {
            enabled: true,
            color: '#000',
            top: 18,
            left: 7,
            blur: 10,
            opacity: 0.2
          },
        },
        dataLabels: {
          enabled: true,
        },
        stroke: {
          curve: 'smooth'
        },
        legend: {
          position: 'right',
          horizontalAlign: 'center',
          floating: false,
          offsetY: 0,
          offsetX: 0,
        },
        grid: {
          borderColor: '#e7e7e7',
          row: {
            colors: ['#f3f3f3', 'transparent'], // takes an array which will be repeated on columns
            opacity: 0.5
          },
        },
        xaxis : {
          categories: this.$store.state.TermspaceProgress.ProgressPerUser.categories
        }
      }
    },
    chartSeries() {
        return this.$store.state.TermspaceProgress.ProgressPerUser.series;
    },
  },
  created() {
  }
};
</script>
