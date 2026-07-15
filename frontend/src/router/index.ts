import {createRouter, createWebHistory, RouteRecordRaw, NavigationGuardNext, RouteLocationNormalized} from 'vue-router';
import HomePage from "../components/HomePage.vue";
import videoDetailPage from "../components/VideoDetailPage.vue";
import CalendarPage from "../components/CalendarPage.vue";
import SearchPage from "../components/SearchPage.vue";


const routes: Array<RouteRecordRaw> = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/LoginPage.vue'),
        meta: { requiresAuth: false }
    },
    {
        path: '/',
        name: 'Home',
        component: HomePage,
        meta: { requiresAuth: true }
    },
    {
        path: '/video/:id',
        name: 'VideoDetail',
        component: videoDetailPage,
        meta: { requiresAuth: true }
    },
    {
        path: '/calendar',
        name: 'Calendar',
        component: CalendarPage,
        meta: { requiresAuth: true }
    },
    {
        path: '/search',
        name: 'Search',
        component: SearchPage,
        meta: { requiresAuth: true }
    },
    {
        path: '/downloads',
        name: 'Downloads',
        component: () => import('../views/Downloads.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/favorites',
        name: 'Favorites',
        component: () => import('../views/Favorites.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/watch-later',
        name: 'WatchLater',
        component: () => import('../views/WatchLater.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/playlists',
        name: 'Playlists',
        component: () => import('../views/Playlists.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/history',
        name: 'WatchHistory',
        component: () => import('../views/WatchHistory.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/changelog',
        name: 'Changelog',
        component: () => import('../views/ChangelogPage.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('../views/NotFound.vue'),
        meta: { requiresAuth: true }
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior() {
        return { top: 0 };
    }
});

const getToken = (): string | null => {
    return localStorage.getItem('token');
};

const isTokenValid = (): boolean => {
    const token = getToken();
    if (!token) return false;
    
    const loginTime = localStorage.getItem('loginTime');
    if (!loginTime) return false;
    
    const expireTime = 24 * 60 * 60 * 1000;
    return Date.now() - parseInt(loginTime) < expireTime;
};

router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
    const requiresAuth = to.meta.requiresAuth !== false;
    const tokenValid = isTokenValid();
    
    if (requiresAuth && !tokenValid) {
        localStorage.removeItem('token');
        localStorage.removeItem('tokenType');
        localStorage.removeItem('username');
        localStorage.removeItem('loginTime');
        
        if (to.path !== '/login') {
            next({ path: '/login', query: { redirect: to.fullPath } });
        } else {
            next();
        }
    } else if (!requiresAuth && tokenValid && to.path === '/login') {
        const redirectPath = from.query.redirect as string || '/';
        next(redirectPath);
    } else {
        next();
    }
});

export default router; 