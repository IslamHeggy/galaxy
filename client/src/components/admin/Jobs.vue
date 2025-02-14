<template>
    <div>
        <h2 id="jobs-title">Jobs</h2>
        <b-alert v-if="this.message !== ''" :variant="galaxyKwdToBootstrap(status)" show>
            {{ message }}
        </b-alert>
        <p>
            Unfinished jobs (in the state 'new', 'queued', 'running', or 'upload') and recently terminal jobs (in the
            state 'error' or 'ok') are displayed on this page. The 'cutoff' input box will limit the display of jobs to
            only those jobs that have had their state updated in the specified timeframe.
        </p>
        <p>
            If any jobs are displayed, you may choose to stop them. Your stop message will be displayed to the user as:
            "This job was stopped by an administrator: <strong>&lt;YOUR MESSAGE&gt;</strong> For more information or
            help, report this error".
        </p>
        <h3>Job Control</h3>
        <job-lock />
        <b-alert v-if="loading" variant="info" show> Waiting for data </b-alert>
        <div v-else>
            <h3>Job Details</h3>
            <b-row>
                <b-col>
                    <b-form name="jobs" @submit.prevent="onRefresh">
                        <b-form-group
                            id="cutoff"
                            label="Cutoff time period"
                            label-for="cutoff-minutes"
                            description="in minutes"
                        >
                            <b-input-group>
                                <b-form-input id="cutoff" type="number" v-model="cutoffMin"> </b-form-input>
                                <b-input-group-append>
                                    <b-btn type="submit">Refresh</b-btn>
                                </b-input-group-append>
                            </b-input-group>
                        </b-form-group>
                    </b-form>
                </b-col>
                <b-col>
                    <b-form-group
                        label="Filter Jobs"
                        label-for="filter-regex"
                        description="by strings or regular expressions"
                    >
                        <b-input-group id="filter-regex">
                            <b-form-input
                                v-model="filter"
                                placeholder="Type to Search"
                                @keyup.esc.native="filter = ''"
                            />
                            <b-input-group-append>
                                <b-btn :disabled="!filter" @click="filter = ''">Clear (esc)</b-btn>
                            </b-input-group-append>
                        </b-input-group>
                    </b-form-group>
                </b-col>
            </b-row>
            <transition name="fade">
                <b-form v-if="unfinishedJobs.length && selectedStopJobIds.length" @submit.prevent="onStopJobs">
                    <b-form-group label="Stop Selected Jobs" description="Stop message will be displayed to the user">
                        <b-input-group>
                            <b-form-input id="stop-message" v-model="stopMessage" placeholder="Stop message" required>
                            </b-form-input>
                            <b-input-group-append>
                                <b-btn type="submit">Submit</b-btn>
                            </b-input-group-append>
                        </b-input-group>
                    </b-form-group>
                </b-form>
            </transition>
            <h4>Unfinished Jobs</h4>
            <b-alert v-if="!unfinishedJobs.length" variant="secondary" show>
                There are no unfinished jobs to show with current cutoff time of {{ cutoffMin }} minutes.
            </b-alert>
            <b-table
                v-else
                v-model="jobsItemsModel"
                :fields="unfinishedJobFields"
                :items="unfinishedJobs"
                :filter="filter"
                hover
                responsive
                striped
                caption-top
                @row-clicked="toggleDetails"
                :busy="busy"
            >
                <template v-slot:table-caption>
                    These jobs are unfinished and have had their state updated in the previous
                    {{ cutoffMin }} minutes. For currently running jobs, the "Last Update" column should indicate the
                    runtime so far.
                </template>
                <template v-slot:head(selected)>
                    <b-form-checkbox
                        v-model="allSelected"
                        :indeterminate="indeterminate"
                        @change="toggleAll"
                    ></b-form-checkbox>
                </template>
                <template v-slot:cell(selected)="data">
                    <b-form-checkbox
                        v-model="selectedStopJobIds"
                        :checked="allSelected"
                        :key="data.index"
                        :value="data.item['id']"
                    ></b-form-checkbox>
                </template>
                <template v-slot:cell(update_time)="data">
                    <utc-date :date="data.value" mode="elapsed" />
                </template>
                <template v-slot:row-details="row">
                    <job-details :job="row.item" />
                </template>
            </b-table>

            <h4>Finished Jobs</h4>
            <b-alert v-if="!finishedJobs.length" variant="secondary" show>
                There are no recently finished jobs to show with current cutoff time of {{ cutoffMin }} minutes.
            </b-alert>

            <b-table
                v-else
                :fields="finishedJobFields"
                :items="finishedJobs"
                :filter="filter"
                hover
                responsive
                striped
                caption-top
                @row-clicked="toggleDetails"
                :busy="busy"
            >
                <template v-slot:table-caption>
                    These jobs have completed in the previous {{ cutoffMin }} minutes.
                </template>
                <template v-slot:cell(update_time)="data">
                    <utc-date :date="data.value" mode="elapsed" />
                </template>
                <template v-slot:row-details="row">
                    <job-details :job="row.item" />
                </template>
            </b-table>
        </div>
    </div>
</template>

<script>
import { getAppRoot } from "onload/loadConfig";
import UtcDate from "components/UtcDate";
import axios from "axios";
import JobDetails from "components/JobInformation/JobDetails";
import JobLock from "./JobLock";
import JOB_STATES_MODEL from "mvc/history/job-states-model";
import { commonJobFields } from "./JobFields";

function cancelJob(jobId, message) {
    const url = `${getAppRoot()}api/jobs/${jobId}`;
    return axios.delete(url, { data: { message: message } });
}

export default {
    components: { UtcDate, JobDetails, JobLock },
    data() {
        return {
            jobs: [],
            finishedJobs: [],
            unfinishedJobs: [],
            jobsItemsModel: [],
            finishedJobFields: [...commonJobFields, { key: "update_time", label: "Finished", sortable: true }],
            unfinishedJobFields: [
                { key: "selected", label: "" },
                ...commonJobFields,
                { key: "update_time", label: "Last Update", sortable: true },
            ],
            selectedStopJobIds: [],
            selectedJobId: null,
            allSelected: false,
            indeterminate: false,
            stopMessage: "",
            filter: "",
            message: "",
            status: "",
            loading: true,
            busy: true,
            cutoffMin: 5,
        };
    },
    watch: {
        selectedStopJobIds(newVal) {
            if (newVal.length === 0) {
                this.indeterminate = false;
                this.allSelected = false;
            } else if (newVal.length === this.jobsItemsModel.length) {
                this.indeterminate = false;
                this.allSelected = true;
            } else {
                this.indeterminate = true;
                this.allSelected = false;
            }
        },
        jobs(newVal) {
            const unfinishedJobs = [];
            const finishedJobs = [];
            newVal.forEach((item) => {
                item._cellVariants = { state: this.translateState(item.state) };
                if (JOB_STATES_MODEL.NON_TERMINAL_STATES.includes(item.state)) {
                    unfinishedJobs.push(item);
                } else {
                    finishedJobs.push(item);
                }
            });
            this.unfinishedJobs = unfinishedJobs;
            this.finishedJobs = finishedJobs;
        },
    },
    methods: {
        update() {
            this.busy = true;
            let params = [];
            const cutoff = Math.floor(this.cutoffMin);
            const dateRangeMin = new Date(Date.now() - cutoff * 60 * 1000).toISOString();
            params.push(`date_range_min=${dateRangeMin}`);
            params.push("view=admin_job_list");
            params = params.join("&");
            axios
                .get(`${getAppRoot()}api/jobs?${params}`)
                .then((response) => {
                    this.jobs = response.data;
                    this.message = response.data.message;
                    this.status = response.data.status;
                    this.loading = false;
                    this.busy = false;
                })
                .catch((error) => {
                    this.message = error.response.data.err_msg;
                    this.status = "error";
                    console.log(error.response);
                });
        },
        onRefresh() {
            this.update();
        },
        onStopJobs() {
            axios.all(this.selectedStopJobIds.map((jobId) => cancelJob(jobId, this.stopMessage))).then((res) => {
                this.update();
                this.selectedStopJobIds = [];
                this.stopMessage = "";
            });
        },

        toggleDetails(item) {
            this.$set(item, "_showDetails", !item._showDetails);
        },
        translateState(state) {
            const translateDict = {
                ok: "success",
                error: "danger",
                new: "primary",
                queued: "secondary",
                running: "info",
                upload: "dark",
            };
            return translateDict[state] || "primary";
        },
        computeItems(items) {
            return items.map((job) => {
                return {
                    ...job,
                    _showDetails: false,
                    _cellVariants: { state: this.translateState(job.state) },
                };
            });
        },
        toggleAll(checked) {
            this.selectedStopJobIds = checked ? this.jobsItemsModel.reduce((acc, j) => [...acc, j["id"]], []) : [];
        },
        galaxyKwdToBootstrap(status) {
            let variant = "info";
            if (status !== "") {
                variant = status;
            }
            const galaxyKwdToBoostrapDict = {
                done: "success",
                info: "info",
                warning: "warning",
                error: "danger",
            };
            if (variant in galaxyKwdToBoostrapDict) {
                return galaxyKwdToBoostrapDict[variant];
            } else {
                return variant;
            }
        },
    },
    created() {
        this.update();
    },
};
</script>

<style>
/* Can not be scoped because of command line tdClass */
.break-word {
    white-space: pre-wrap;
    word-break: break-word;
}
.info-frame-container {
    overflow: hidden;
    padding-top: 100%;
    position: relative;
}
.info-frame-container iframe {
    border: 0;
    height: 100%;
    left: 0;
    position: absolute;
    top: 0;
    width: 100%;
}
</style>
