function [X, foot_goals] = footstepLineSearch(biped, foot_orig, goal_pos, params)

debug = false;
X = createOriginSteps(biped, foot_orig, params.right_foot_lead);
foot_orig.right(4:5) = 0;
foot_orig.left(4:5) = 0;


p0 = footCenter2StepCenter(biped, X(2).pos, X(2).is_right_foot, params.nom_step_width);
goal_pos(6) = p0(6) + angleDiff(p0(6), goal_pos(6));
goal_pos(3,:) = p0(3);
if ~params.ignore_terrain
  goal_pos = fitStepToTerrain(biped, goal_pos);
end

if params.follow_spline
  traj = BezierTraj([p0, goal_pos]);
else
  traj = DirectTraj([p0, goal_pos]);
end


lambdas = linspace(0, 1, 200);
traj_poses = traj.eval(lambdas);
if any(any(isnan(traj_poses)))
  error(['Got bad footstep trajectory data (NaN) at time: ', datestr(now())]);
end
foot_centers = struct('right', biped.stepCenter2FootCenter(traj_poses, 1, params.nom_step_width),...
                      'left', biped.stepCenter2FootCenter(traj_poses, 0, params.nom_step_width));
if params.check_feasibility
  contacts = biped.getBody(biped.foot_bodies_idx(1)).contact_pts; % just use r foot for now
  % feas_check is a function which we can call on a list of poses and which returns 1 for safe terrain and 0 for unsafe terrain
  feas_check = biped.getTerrain().getStepFeasibilityChecker(contacts, struct('debug', false));
else
  feas_check = @(xyzrpy) ones(1, size(xyzrpy, 2));
end
for f = {'left', 'right'}
  ft = f{1};
  feasibility.(ft) = feas_check(foot_centers.(ft)([1:2,6],:));
end
if params.ignore_terrain
  % use position of the right foot to set the height and orientation of the steps
  normal = rpy2rotmat(p0(4:6)) * [0;0;1];
  foot_centers.right(3,:) = p0(3) - (1 / normal(3)) * (normal(1) * (foot_centers.right(1,:) - p0(1)) + normal(2) * (foot_centers.right(2,:) - p0(2)));
  foot_centers.left(3,:) = p0(3) - (1 / normal(3)) * (normal(1) * (foot_centers.left(1,:) - p0(1)) + normal(2) * (foot_centers.left(2,:) - p0(2)));
  foot_centers.right = fitPoseToNormal(foot_centers.right, repmat(normal, 1, length(foot_centers.right(1,:))));
  foot_centers.left = fitPoseToNormal(foot_centers.left, repmat(normal, 1, length(foot_centers.right(1,:))));
  feasibility.right = ones(size(feasibility.right));
  feasibility.left = ones(size(feasibility.left));
else
  for f = {'right', 'left'}
    foot = f{1};
    foot_centers.(foot) = fitStepToTerrain(biped, foot_centers.(foot));
  end
end

last_safe_idx = find(feasibility.right & feasibility.left, 1, 'last');
foot_goals = struct('right', foot_centers.right(:, last_safe_idx), 'left', foot_centers.left(:, last_safe_idx));

if debug
  ls = linspace(0, 1);
  xy = traj.eval(ls);
  plot_lcm_points([xy(1,:)', xy(2,:)', xy(3,:)'], repmat([0, 0, 1], length(ls), 1), 50, 'Foostep Spline', 2, 1);
end

last_ndx = struct('right', 1, 'left', 1);
  
stall = struct('right', 0, 'left', 0);
aborted = false;
min_progress = [0.05;0.05;1;0.2;0.2;0.03];
% n = 0;
  
while (1)
  is_right_foot = ~X(end).is_right_foot;
  if is_right_foot
    m_foot = 'right';
    s_foot = 'left';
  else
    m_foot = 'left';
    s_foot = 'right';
  end
  if isempty(foot_goals.(m_foot))
    break
  end

  potential_poses = foot_centers.(m_foot)(:, last_ndx.(m_foot):end);
  % feas_opts = struct('forward_step', params.nom_forward_step,...
  %                    'nom_step_width', params.nom_step_width);
  feas_opts = params;
  feas_opts.forward_step = params.nom_forward_step;
  reach = biped.checkStepReach(X(end).pos, potential_poses, ~is_right_foot, feas_opts);
  valid_pose_ndx = find(max(reach, [], 1) <= 0 & feasibility.(m_foot)(last_ndx.(m_foot):end)) + (last_ndx.(m_foot) - 1);
  if isempty(valid_pose_ndx)
    novalid = true;
  else
    novalid = false;
    if (...
        all(abs(X(end).pos - foot_goals.(s_foot)) < 0.05) || ...
        (...
         ((length(X) - 2) >= params.max_num_steps - 1) && ...
         (params.max_num_steps > 1)...
        )...
       )
      [~, j] = min(abs(valid_pose_ndx - last_ndx.(s_foot)));
      next_ndx = valid_pose_ndx(j);
    else
      next_ndx = valid_pose_ndx(end);
    end
    noprogress = all(abs(foot_centers.(m_foot)(:, next_ndx) - foot_centers.(m_foot)(:,last_ndx.(m_foot))) < min_progress);
  end

  if (novalid || noprogress)
    % Try again with a longer maximum step
    feas_opts.forward_step = params.max_forward_step;
    reach = biped.checkStepReach(X(end).pos, potential_poses, ~is_right_foot, feas_opts);
    valid_pose_ndx = find(max(reach, [], 1) <= 0 & feasibility.(m_foot)(last_ndx.(m_foot):end)) + last_ndx.(m_foot) - 1;
    if isempty(valid_pose_ndx)
      novalid = true;
      next_ndx = last_ndx.(m_foot);
    else
      if novalid
        next_ndx = valid_pose_ndx(1);
      else
        n = find(valid_pose_ndx > next_ndx, 1, 'first');
        if ~isempty(n)
          next_ndx = valid_pose_ndx(n);
        else
          next_ndx = valid_pose_ndx(end);
        end
      end
      novalid = false;
      noprogress = all(abs(foot_centers.(m_foot)(:, next_ndx) - foot_centers.(m_foot)(:,last_ndx.(m_foot))) < min_progress);
    end      
  end

  if (novalid || noprogress)
    stall.(m_foot) = stall.(m_foot) + 1;
    if (novalid || stall.(m_foot) >= 2 || (stall.(m_foot) > 0 && stall.(s_foot) > 0)) && (length(X) - 3 >= params.min_num_steps)
      aborted = true;
      break
    end
  else
    stall.(m_foot) = 0;
  end

  pos_n = foot_centers.(m_foot)(:, next_ndx);
  last_ndx.(m_foot) = next_ndx;

  X(end+1) = struct('pos', pos_n, 'is_right_foot', is_right_foot);

  if ((all(abs(X(end).pos - foot_goals.(m_foot)) < 0.05) && all(abs(X(end-1).pos - foot_goals.(s_foot)) < 0.05)) || (length(X) - 2) >= params.max_num_steps) && ((length(X) - 2) >= params.min_num_steps)
    break
  end
end

if aborted && length(X) > 3
  % If we had to give up, then lose the last (unproductive) step
  X = X(1:end-1);
end

end
