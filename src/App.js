import React, { lazy } from 'react';

// Implement React.lazy for route-based code splitting
const DisasterMap = lazy(() => import('./components/DisasterMap'));

export default DisasterMap; 