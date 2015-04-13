classdef SilentPlan < QPControllerPlan
  methods
    function obj = SilentPlan(robot)
      obj.default_qp_input = atlasControllers.QPInputConstantHeight();
      obj.default_qp_input.be_silent = true;
      obj.default_qp_input.whole_body_data.q_des = zeros(robot.getNumPositions(), 1);
    end

    function qp_input = getQPControllerInput(obj, varargin)
      qp_input = obj.default_qp_input;
    end
  end
end