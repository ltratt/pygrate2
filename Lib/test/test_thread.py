import os
import unittest
import random
from test import support
from test.test_support import check_py3k_warnings
thread = support.import_module('thread')
import time
import sys
import weakref
import warnings

from test import lock_tests

NUMTASKS = 10
NUMTRIPS = 3


_print_mutex = thread.allocate_lock()

def verbose_print(arg):
    """Helper function for printing out debugging output."""
    if support.verbose:
        with _print_mutex:
            print arg



class BasicThreadTest(unittest.TestCase):

    def setUp(self):
        self.done_mutex = thread.allocate_lock()
        self.done_mutex.acquire()
        self.running_mutex = thread.allocate_lock()
        self.random_mutex = thread.allocate_lock()
        self.created = 0
        self.running = 0
        self.next_ident = 0

        key = support.threading_setup()
        self.addCleanup(support.threading_cleanup, *key)


class ThreadRunningTests(BasicThreadTest):

    def newtask(self):
        with self.running_mutex:
            self.next_ident += 1
            verbose_print("creating task %s" % self.next_ident)
            thread.start_new_thread(self.task, (self.next_ident,))
            self.created += 1
            self.running += 1

    def task(self, ident):
        with self.random_mutex:
            delay = random.random() / 10000.0
        verbose_print("task %s will run for %sus" % (ident, round(delay*1e6)))
        time.sleep(delay)
        verbose_print("task %s done" % ident)
        with self.running_mutex:
            self.running -= 1
            if self.created == NUMTASKS and self.running == 0:
                self.done_mutex.release()

    def test_starting_threads(self):
        with support.wait_threads_exit():
            # Basic test for thread creation.
            for i in range(NUMTASKS):
                self.newtask()
            verbose_print("waiting for tasks to complete...")
            self.done_mutex.acquire()
            verbose_print("all tasks done")

    def test_stack_size(self):
        # Various stack size tests.
        self.assertEqual(thread.stack_size(), 0, "initial stack size is not 0")

        thread.stack_size(0)
        self.assertEqual(thread.stack_size(), 0, "stack_size not reset to default")

    @unittest.skipIf(os.name not in ("nt", "os2", "posix"), 'test meant for nt, os2, and posix')
    def test_nt_and_posix_stack_size(self):
        try:
            thread.stack_size(4096)
        except ValueError:
            verbose_print("caught expected ValueError setting "
                            "stack_size(4096)")
        except thread.error:
            self.skipTest("platform does not support changing thread stack "
                          "size")

        fail_msg = "stack_size(%d) failed - should succeed"
        for tss in (262144, 0x100000, 0):
            thread.stack_size(tss)
            self.assertEqual(thread.stack_size(), tss, fail_msg % tss)
            verbose_print("successfully set stack_size(%d)" % tss)

        for tss in (262144, 0x100000):
            verbose_print("trying stack_size = (%d)" % tss)
            self.next_ident = 0
            self.created = 0
            with support.wait_threads_exit():
                for i in range(NUMTASKS):
                    self.newtask()

                verbose_print("waiting for all tasks to complete")
                self.done_mutex.acquire()
                verbose_print("all tasks done")

        thread.stack_size(0)

    def test__count(self):
        # Test the _count() function.
        orig = thread._count()
        mut = thread.allocate_lock()
        mut.acquire()
        started = []

        def task():
            started.append(None)
            mut.acquire()
            mut.release()

        with support.wait_threads_exit():
            thread.start_new_thread(task, ())
            while not started:
                time.sleep(0.01)
            self.assertEqual(thread._count(), orig + 1)
            # Allow the task to finish.
            mut.release()
            # The only reliable way to be sure that the thread ended from the
            # interpreter's point of view is to wait for the function object to be
            # destroyed.
            done = []
            wr = weakref.ref(task, lambda _: done.append(None))
            del task
            while not done:
                time.sleep(0.01)
            self.assertEqual(thread._count(), orig)

    def test_save_exception_state_on_error(self):
        # See issue #14474
        def task():
            started.release()
            raise SyntaxError
        def mywrite(self, *args):
            try:
                raise ValueError
            except ValueError:
                pass
            real_write(self, *args)
        c = thread._count()
        started = thread.allocate_lock()
        with support.captured_output("stderr") as stderr:
            real_write = stderr.write
            stderr.write = mywrite
            started.acquire()
            with support.wait_threads_exit():
                thread.start_new_thread(task, ())
                started.acquire()
        self.assertIn("Traceback", stderr.getvalue())

    def test_py3k_thread_module(self):
        if sys.py3kwarning:
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings('always', category=Py3xWarning)
                import thread

    def test_py3k_thread_module_get_ident(self):
        if sys.py3kwarning:
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings('always', category=Py3xWarning)
                thread.get_ident()

    def test_py3k_thread_module_start_new_thread(self):
        if sys.py3kwarning:
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings('always', category=Py3xWarning)
                def f():
                    ident.append(threading.currentThread().ident)
                    done.set()
                thread.start_new_thread((f), ())

    def test_py3k_thread_module_allocate(self):
        if sys.py3kwarning:
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings('always', category=Py3xWarning)
                thread.allocate_lock()

    def test_py3k_thread_module_exit_thread(self):
        if sys.py3kwarning:
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings('always', category=Py3xWarning)
                with self.assertRaises(SystemExit):
                    thread.exit_thread()

    def test_py3k_thread_module_interrupt_main(self):
        if sys.py3kwarning:
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings('always', category=Py3xWarning)
                with self.assertRaises(KeyboardInterrupt):
                    thread.interrupt_main()

    def test_py3k_thread_module_count(self):
        if sys.py3kwarning:
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings('always', category=Py3xWarning)
                thread._count()

    def test_py3k_thread_module_stack_size(self):
        if sys.py3kwarning:
            with warnings.catch_warnings(record=True) as w:
                warnings.filterwarnings('always', category=Py3xWarning)
                thread.stack_size()


class Barrier:
    def __init__(self, num_threads):
        self.num_threads = num_threads
        self.waiting = 0
        self.checkin_mutex  = thread.allocate_lock()
        self.checkout_mutex = thread.allocate_lock()
        self.checkout_mutex.acquire()

    def enter(self):
        self.checkin_mutex.acquire()
        self.waiting = self.waiting + 1
        if self.waiting == self.num_threads:
            self.waiting = self.num_threads - 1
            self.checkout_mutex.release()
            return
        self.checkin_mutex.release()

        self.checkout_mutex.acquire()
        self.waiting = self.waiting - 1
        if self.waiting == 0:
            self.checkin_mutex.release()
            return
        self.checkout_mutex.release()


class BarrierTest(BasicThreadTest):

    def test_barrier(self):
        with support.wait_threads_exit():
            self.bar = Barrier(NUMTASKS)
            self.running = NUMTASKS
            for i in range(NUMTASKS):
                thread.start_new_thread(self.task2, (i,))
            verbose_print("waiting for tasks to end")
            self.done_mutex.acquire()
            verbose_print("tasks done")

    def task2(self, ident):
        for i in range(NUMTRIPS):
            if ident == 0:
                # give it a good chance to enter the next
                # barrier before the others are all out
                # of the current one
                delay = 0
            else:
                with self.random_mutex:
                    delay = random.random() / 10000.0
            verbose_print("task %s will run for %sus" %
                          (ident, round(delay * 1e6)))
            time.sleep(delay)
            verbose_print("task %s entering %s" % (ident, i))
            self.bar.enter()
            verbose_print("task %s leaving barrier" % ident)
        with self.running_mutex:
            self.running -= 1
            # Must release mutex before releasing done, else the main thread can
            # exit and set mutex to None as part of global teardown; then
            # mutex.release() raises AttributeError.
            finished = self.running == 0
        if finished:
            self.done_mutex.release()


class LockTests(lock_tests.LockTests):
    locktype = thread.allocate_lock


class TestForkInThread(unittest.TestCase):
    def setUp(self):
        self.read_fd, self.write_fd = os.pipe()

    @unittest.skipIf(sys.platform.startswith('win'),
                     "This test is only appropriate for POSIX-like systems.")
    @support.reap_threads
    def test_forkinthread(self):
        non_local = {'status': None}
        def thread1():
            try:
                pid = os.fork() # fork in a thread
            except RuntimeError:
                sys.exit(0) # exit the child

            if pid == 0: # child
                os.close(self.read_fd)
                os.write(self.write_fd, "OK")
                # Exiting the thread normally in the child process can leave
                # any additional threads (such as the one started by
                # importing _tkinter) still running, and this can prevent
                # the half-zombie child process from being cleaned up. See
                # Issue #26456.
                os._exit(0)
            else: # parent
                os.close(self.write_fd)
                pid, status = os.waitpid(pid, 0)
                non_local['status'] = status

        with support.wait_threads_exit():
            thread.start_new_thread(thread1, ())
            self.assertEqual(os.read(self.read_fd, 2), "OK",
                             "Unable to fork() in thread")
        self.assertEqual(non_local['status'], 0)

    def tearDown(self):
        try:
            os.close(self.read_fd)
        except OSError:
            pass

        try:
            os.close(self.write_fd)
        except OSError:
            pass


def test_main():
    support.run_unittest(ThreadRunningTests, BarrierTest, LockTests,
                              TestForkInThread)

if __name__ == "__main__":
    test_main()
