double global_joules_consumed(void)
{
	bool global_discharging = false;
	double total = 0.0;
	unsigned int i;

	for (i = 0; i < power_meters.size(); i++) {
		global_discharging |= power_meters[i]->is_discharging();
		total += power_meters[i]->joules_consumed();
	}
	/* report global time left if at least one battery is discharging */
	if (!global_discharging)
		return 0.0;

	all_results.power = total;
	if (total < min_power && total > 0.01)
		min_power = total;
	return total;
}

double global_time_left(void)
{
	bool global_discharging = false;
	double total_capacity = 0.0;
	double total_rate = 0.0;
	unsigned int i;
	for (i = 0; i < power_meters.size(); i++) {
		global_discharging |= power_meters[i]->is_discharging();
		total_capacity += power_meters[i]->dev_capacity();
		total_rate += power_meters[i]->joules_consumed();
	}
	/* report global time left if at least one battery is discharging */
	if (!global_discharging)
		return 0.0;

	/* return 0.0 instead of INF+ */
	if (total_rate < 0.001)
		return 0.0;
	return total_capacity / total_rate;
}
