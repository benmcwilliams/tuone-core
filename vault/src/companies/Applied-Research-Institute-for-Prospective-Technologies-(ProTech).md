```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Applied-Research-Institute-for-Prospective-Technologies-(ProTech)" or company = "Applied Research Institute for Prospective Technologies (ProTech)")
sort location, dt_announce desc
```
