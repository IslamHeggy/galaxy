<template>
    <div>
        <div v-for="contentItem in collectionContents" :index="1" :key="contentItem.id" style="margin-left: 2em">
            <DatasetProvider
                v-if="contentItem.element_type === 'hda'"
                :id="contentItem.object.id"
                v-slot="{ item, loading }"
            >
                <div>
                    <loading-span v-if="loading" message="Loading datasets" />
                    <DatasetUIWrapper v-else :item="item" :element_identifier="contentItem.element_identifier">
                    </DatasetUIWrapper>
                </div>
            </DatasetProvider>
            <DatasetCollectionUIWrapper
                v-if="contentItem.element_type === 'dataset_collection'"
                :item="contentItem"
                :element_count="collectionContents.length + 1"
            >
            </DatasetCollectionUIWrapper>
        </div>
    </div>
</template>
<script>
import { DatasetProvider } from "components/providers";
import DatasetUIWrapper from "./DatasetUIWrapper";
import LoadingSpan from "components/LoadingSpan";

export default {
    components: {
        DatasetProvider,
        DatasetCollectionUIWrapper: () => import("./DatasetCollectionUIWrapper"),
        DatasetUIWrapper,
        LoadingSpan,
    },
    props: {
        collectionContents: { type: Array, required: true },
    },
};
</script>
