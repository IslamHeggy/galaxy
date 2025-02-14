import { mount } from "@vue/test-utils";
import { getLocalVue } from "jest/helpers";
import FormDefault from "./FormDefault";
import { ActiveOutputs } from "components/Workflow/Editor/modules/outputs";

const localVue = getLocalVue();

describe("FormDefault", () => {
    let wrapper;
    const activeOutputs = new ActiveOutputs();
    const outputs = [
        { name: "output-name", label: "output-label" },
        { name: "other-name", label: "other-label" },
    ];

    beforeEach(() => {
        activeOutputs.initialize(outputs);
        wrapper = mount(FormDefault, {
            propsData: {
                datatypes: [],
                getManager: () => {
                    return {
                        nodes: [],
                    };
                },
                getNode: () => {
                    return {
                        name: "node-title",
                        type: "subworkflow",
                        outputs: outputs,
                        activeOutputs: activeOutputs,
                        config_form: {
                            inputs: [],
                        },
                    };
                },
            },
            localVue,
        });
    });

    it("check initial value and value change", async () => {
        const title = wrapper.find(".portlet-title-text").text();
        expect(title).toBe("node-title");
        const inputCount = wrapper.findAll("input").length;
        expect(inputCount).toBe(3);
        const outputLabelCount = wrapper.findAll("div[tour_id='__label__output-name']").length;
        expect(outputLabelCount).toBe(1);
        const otherLabelCount = wrapper.findAll("div[tour_id='__label__other-name']").length;
        expect(otherLabelCount).toBe(1);
    });
});
